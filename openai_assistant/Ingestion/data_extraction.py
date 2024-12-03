import zipfile
import re
import pdfplumber
# import docx
import pandas as pd



class DataExtract:
    def __init__(self, data_path) -> None:
        self.data_path = data_path
    def merge_hypernated_words(self, text):
        return re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    def fix_newlines(self, text):
        return re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    def remove_multiple_newlines(self, text):
        return re.sub(r"\n{2,}", "\n", text)
    def clean_text(self, text):
        cleaning_functions = [
            self.merge_hypernated_words,
            self.fix_newlines,
            self.remove_multiple_newlines
            ]
        
        for cf in cleaning_functions:
            text = cf(text)
        return text
    
    def read_meta_from_zip_file(self):
        meta_file_name = "Risk_and_policies.xlsx"
        with zipfile.ZipFile(self.data_path, 'r') as zip_ref:
            with zip_ref.open(meta_file_name) as csv_file:
                print(f"read_meta_from_zip_file {meta_file_name}")
                meta_df = pd.read_excel(csv_file)
                meta_df["Published"] = meta_df["Published"].apply(pd.to_datetime)
                meta_df["Published"] = meta_df['Published'].dt.strftime('%d-%m-%Y')

                result_json = meta_df.to_dict(orient='records')
        return result_json
    
    def read_from_zip_file(self, file_name):
        with zipfile.ZipFile(self.data_path, 'r') as zip_ref:
            with zip_ref.open(file_name) as file_path:
                if file_name.lower().endswith('.pdf'):
                    print(f"read_from_zip_file {file_name}")
                    with pdfplumber.open(file_path) as pdf:
                        text_pages = []
                        for page_num, page in enumerate(pdf.pages):
                            text = page.extract_text()
                            clean_text = self.clean_text(text)
                            text_pages.append((page_num + 1, clean_text))

                    return text_pages
                # elif file_name.lower().endswith('.docx'):
                #     data = []
                #     doc = docx.Document(file_path)
                #     for paragraph in doc.paragraphs:
                #         data.append(paragraph.text)
                #     return data