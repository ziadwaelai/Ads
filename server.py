from flask import Flask, request, jsonify
from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
import base64
import os
from dotenv import dotenv_values
env = dotenv_values(".env")
os.environ["OPENAI_API_KEY"] = env["OPENAI_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = env["LANGCHAIN_API_KEY"]

app = Flask(__name__)
model= ChatOpenAI(model='gpt-4o-mini',temperature=0.1, max_tokens=10)


def is_suitable_text(text, model):
    template = """
    Given the following text:
    "{text}"
    Please check if the Text contains any offensive or inappropriate language (bad words) or has a not resspectful tone and reply only with `suitable` or `not suitable`.
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    return True if chain.invoke({"text": text}).content.lower() == "suitable" else False

def is_titleDescription_consistent(title, description, model):
    template = """
        Given the following title and description for the same product on an e-commerce website:
        Title: {title}
        Description: {description}
        Please check if the title and description are generally related to the same product, even if one is more specific or detailed than the other. 
        Respond with `consistent` if they are related, and `not consistent` if they are not.
        """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    return True if chain.invoke({"title": title, "description": description}).content.lower() == "consistent" else False

def encode_image(image_file):
    try:
        if isinstance(image_file, str):
            # If image_file is a file path
            with open(image_file, "rb") as file:
                encoded_string = base64.b64encode(file.read()).decode("utf-8")
        else:
            # If image_file is a file-like object
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string
    except Exception as e:
        # Handle exceptions such as file not found or read errors
        print(f"An error occurred while encoding the image: {e}")
        return None

def is_imageTitle_consistent(title, base64_image, model):
    prompt=f'check is the image related to the title "{title}" and reply only with `consistent` or `not consistent`.'
    message = [HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                },
            },
            {"type": "text", "text": prompt},
    ])]
    response = model.invoke(message)
    return True if response.content.lower() == "consistent" else False

def is_image_safe(base64_image, model):
    prompt= """
        Please analyze the image and check if it contains any of the following:
        - Weapons
        - Medical tools or TABLETS
        - Drugs or drug-related items
        - Nudity or explicit content
        - Violence or blood
        - Hate symbols or offensive content

        If any of these categories are present in the image, respond with "Not safe". If the image is free of these items, respond with "Safe".
        """
    message = [HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                },
            },
            {"type": "text", "text": prompt},
    ])]
    response = model.invoke(message)
    return True if response.content.lower() == "safe" else False

def is_image_watermarked(base64_image, model):
    prompt = """
    Please analyze the image and check if it contains any watermarks or logos. 
    If the image contains a watermark or logo, respond with "Watermarked" only. 
    If the image does not contain any watermarks or logos, respond with "Not watermarked" only.
    """
    message = [HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                },
            },
            {"type": "text", "text": prompt},
    ])]
    response = model.invoke(message)
    return True if response.content.lower() == "watermarked" or response.content.lower() == "Watermarked." else False

def is_person_in_image(base64_image, model):
    prompt = """
    Please analyze the image and check if it contains a full person (not just a hand ). 
    If a full person is present in the image, respond with "Person". 
    If the image does not contain a person or only contains a partial body (like a hand or arm), respond with "No person".
    """

    message = [HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                },
            },
            {"type": "text", "text": prompt},
    ])]
    response = model.invoke(message)
    return True if response.content.lower() == "person" else False

def is_titleCategory_consistent(title, category, model):
    template = """
    Given the following title and category for a product on an e-commerce website:
    Title: {title}
    Category: {category}
    now check if the title and category are related to each other, 
    and reply only with `consistent` or `not consistent`.
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    return True if chain.invoke({"title": title, "category": category}).content.lower() == "consistent" else False

@app.route('/check_ad', methods=['POST'])
def check_ad():
    try:
        data = request.form
        title = data.get("title")
        description = data.get("description")
        catgory = data.get("category")
        images = request.files.getlist("images")
    except Exception as e:
        return jsonify({"error": f"Invalid request data: {e}"}), 400
    
    try:
        
        if not title or not description or not catgory or not images:
            return jsonify({"error": "Please provide title, description, category and images"}), 400
        
        if not is_suitable_text(title, model):
            return jsonify({"error": "Title contains inappropriate language"}), 400
        
        if not is_titleCategory_consistent(title, catgory, model):
            return jsonify({"error": "Title and category are not consistent"}), 400
        
        if not is_suitable_text(description, model):
            return jsonify({"error": "Description contains inappropriate language"}), 400
        
        if not is_titleDescription_consistent(title, description, model):
            return jsonify({"error": "Title and description are not consistent"}), 400
        
    except Exception as e:
        return jsonify({"error": f"An error occurred while processing the text data: {e}"}), 500
    try:
        for image in images:
            base64_image = encode_image(image)
            if not base64_image:
                return jsonify({"error": "An error occurred while encoding the image"}), 500
            
            if not is_image_safe(base64_image, model):
                return jsonify({"error": "Image is not safe"}), 400
            
            if is_image_watermarked(base64_image, model):
                return jsonify({"error": "Image is watermarked"}), 400
            
            if is_person_in_image(base64_image, model) and (catgory.lower() != "jobs" or catgory.lower() != "fashions"):
                return jsonify({"error": "Image does contain a person"}), 400
            
            if not is_imageTitle_consistent(title, base64_image, model):
                return jsonify({"error": "Image is not consistent with the title"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred while processing the images: {e}"}), 500
        
    return jsonify({"message": "Ad is suitable"}), 200

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"An error occurred while running the server: {e}")