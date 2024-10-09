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

def create_prompt(code_content, pdf_content, image_files):
    code_summary = code_content[:500] + "..." if len(code_content) > 500 else code_content
    pdf_summary = pdf_content[:500] + "..." if len(pdf_content) > 500 else pdf_content

    image_descriptions = "\n".join([f"- {os.path.basename(img)}" for img in image_files])
    prompt = f"""AI 어시스턴트로서, 제공된 소스 코드와 발표 자료를 바탕으로 GitHub README를 한국어로 작성해 주세요.
    다음 섹션을 포함해 주세요: 프로젝트 설명, 주요 기능, 설치 가이드, 사용 예시, 테스트, 배포, 기여 방법, 라이선스, 감사의 말.

    소스 코드 요약:
    ```
    {code_summary}
    ```

    발표 자료 요약:
    {pdf_summary}

    추출된 이미지 파일:
    {image_descriptions}

    README 작성 시 다음 사항을 고려해 주세요:
    1. **중요한 단어나 구문**은 볼드체로 강조해 주세요.
    2. 각 섹션에 적절한 이모티콘을 사용하세요.
    3. 다양한 Markdown 요소를 활용하여 가독성을 높여주세요.
    4. 전문적이면서도 친근한 톤으로 작성해 주세요.
    5. 이미지를 포함할 때는 다음 형식을 사용하세요: ![이미지 설명](images/이미지 파일명)
    6. 이미지를 포함할 때는 해당 이미지가 어떤 내용을 나타내는지 간단히 설명해 주세요."""
    return prompt

def generate_readme(source_code, presentation_text, image_files):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    prompt = create_prompt(source_code, presentation_text, image_files)
    few_shot_examples = [
        {
            "role": "user",
            "content": "Python 기반 데이터 분석 프로젝트를 위한 GitHub README를 작성해 주세요. 프로젝트 로고 이미지가 'images/logo.png'에 있습니다."
        },
        {
            "role": "assistant",
            "content": """# 📊 데이터 분석 도구

![프로젝트 로고](images/logo.png)

## 🔍 프로젝트 설명
이 프로젝트는 **대규모 데이터 집합**을 분석하고, **통계적 인사이트**를 도출하기 위해 설계된 Python 기반 데이터 분석 도구입니다.

## ✨ 주요 기능
- 🧹 **데이터 처리**: 데이터 정리, 변환 및 필터링
- 📈 **시각화**: 다양한 형식으로 그래프 생성
- 🧮 **통계 분석**: 평균, 분산 등 기본 통계 계산

## 🛠 설치 가이드
1. 저장소를 복제합니다:
   ```bash
   git clone https://github.com/username/data-analysis-tool.git
   ```
2. 필요한 패키지를 설치합니다:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 사용 예시
```python
from data_analysis_tool import DataAnalyzer

analyzer = DataAnalyzer('data.csv')
results = analyzer.analyze()
analyzer.visualize(results, 'output.png')
```

## 📄 라이선스
이 프로젝트는 **MIT 라이선스** 하에 배포됩니다."""
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
    readme_content = generate_readme(source_code, presentation_text, image_files)
    
    return readme_content