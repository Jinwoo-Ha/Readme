import os
from PyPDF2 import PdfReader
import fitz  # PyMuPDF
from openai import OpenAI
from django.conf import settings
from django.core.files.base import ContentFile

def extract_images_from_pdf(pdf_path, image_folder):
    os.makedirs(image_folder, exist_ok=True)
    
    pdf_document = fitz.open(pdf_path)
    image_files = []
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_name = f"image_{page_num+1}_{img_index+1}.{image_ext}"
            image_path = os.path.join(image_folder, image_name)
            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)
            image_files.append(image_path)
    return image_files

def extract_text_from_pdf(pdf_path):
    pdf_reader = PdfReader(pdf_path)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def create_prompt(code_content, pdf_content, image_files, title, description):
    code_summary = code_content[:500] + "..." if len(code_content) > 500 else code_content
    pdf_summary = pdf_content[:500] + "..." if len(pdf_content) > 500 else pdf_content

    image_descriptions = "\n".join([f"- {os.path.basename(img)}" for img in image_files])
    prompt = f"""As an AI assistant, please create a GitHub README in English based on the provided source code and presentation materials.
    
    Project Title: {title}
    Project Description: {description}
    
    Please include the following sections: Project Description, Key Features, Installation Guide, Usage Examples, Testing, Deployment, How to Contribute, License, and Acknowledgments.

    Source Code Summary:
    ```
    {code_summary}
    ```

    Presentation Summary:
    {pdf_summary}

    Extracted Image Files:
    {image_descriptions}

    Please consider the following when writing the README:
    1. Use the provided project title for the README title.
    2. Base the project description section on the provided description, supplemented with information from other sources.
    3. Use **bold text** to emphasize important words or phrases.
    4. Include appropriate emojis for each section.
    5. Utilize various Markdown elements to enhance readability.
    6. Write in a professional yet friendly tone.
    7. When including images, use the following format: ![image description](images/image_filename)
    8. When including images, briefly explain what each image represents."""
    return prompt

def generate_readme(source_code, presentation_text, image_files, project_title, project_description):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    prompt = create_prompt(source_code, presentation_text, image_files, project_title, project_description)
    few_shot_examples = [
        {
            "role": "user",
            "content": "Please create a GitHub README for a Python-based data analysis project. The project logo is located at 'images/logo.png'."
        },
        {
            "role": "assistant",
            "content": """# 📊 Data Analysis Tool

## 🔍 Project Title
Python data analysis project
            
![Project Logo](images/logo.png)

## 🔍 Project Description
This project is a Python-based data analysis tool designed to analyze **large datasets** and derive **statistical insights**.

## ✨ Key Features
- 🧹 **Data Processing**: Clean, transform, and filter data
- 📈 **Visualization**: Generate graphs in various formats
- 🧮 **Statistical Analysis**: Calculate basic statistics including mean, variance, etc.

## 🛠 Installation Guide
1. Clone the repository:
   ```bash
   git clone https://github.com/username/data-analysis-tool.git
   ```
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage Example
```python
from data_analysis_tool import DataAnalyzer

analyzer = DataAnalyzer('data.csv')
results = analyzer.analyze()
analyzer.visualize(results, 'output.png')
```

## 📄 License
This project is distributed under the **MIT License**."""
        }
    ]
    messages = few_shot_examples + [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=1500
    )
    
    return response.choices[0].message.content

def process_uploaded_files(document):
    # Extract images from PDF
    pdf_path = os.path.join(settings.MEDIA_ROOT, document.presentation.name)
    image_folder = os.path.join(settings.MEDIA_ROOT, 'images')
    image_files = extract_images_from_pdf(pdf_path, image_folder)
    
    # Extract text from PDF
    presentation_text = extract_text_from_pdf(pdf_path)
    
    # Read source code
    source_code_path = os.path.join(settings.MEDIA_ROOT, document.source_code.name)
    encodings = ['utf-8', 'cp949', 'euc-kr']
    for encoding in encodings:
        try:
            with open(source_code_path, 'r', encoding=encoding) as file:
                source_code = file.read()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Unable to decode the source code file with any known encoding")
    
    # Generate README
    # README 생성 부분 수정
    readme_content = generate_readme(source_code, presentation_text, image_files, document.project_title, document.project_description)    
    return readme_content