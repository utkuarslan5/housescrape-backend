from googletrans import Translator, LANGUAGES
from pydantic import BaseModel, ValidationError
import pandas as pd
import modal


stub = modal.Stub("google-translator")
translate_image = modal.Image.debian_slim(python_version="3.10").run_commands(
    "apt-get update",
    'pip install "googletrans==4.0.0-rc1" pydantic pandas',
)

# @TODO: add Pydantic V2
class TranslationInput(BaseModel):
    text: str
    dest_language: str = 'en'

    @property
    def is_valid_language(self):
        return self.dest_language in LANGUAGES
    
def translate_text(translation_input: TranslationInput):
    """
    Translates the given text to the specified destination language.

    Parameters:
    translation_input (TranslationInput): An instance of TranslationInput containing text and destination language.

    Returns:
    str: Translated text.
    """
    if not translation_input.is_valid_language:
        raise ValueError(f"Invalid destination language: {translation_input.dest_language}")

    translator = Translator()
    try:
        translated = translator.translate(translation_input.text, dest=translation_input.dest_language)
        return translated.text
    except Exception as e:
        return f"Translation Error: {e}"
    
@stub.function(image=translate_image)
def translate_property_descriptions(df: pd.DataFrame, column_name: str):
    """
    Translates the descriptions in a DataFrame column to English.

    Parameters:
    df (pd.DataFrame): DataFrame containing property data.
    column_name (str): The name of the column containing text to translate.

    Returns:
    pd.DataFrame: DataFrame with an additional column for translated text.
    """
    translated_texts = []
    for text in df[column_name]:
        try:
            translation_input = TranslationInput(text=text)
            translated_text = translate_text(translation_input)
            translated_texts.append(translated_text)
        except ValidationError as e:
            translated_texts.append(f"Validation Error: {e}")
        except ValueError as e:
            translated_texts.append(str(e))

    df[f'{column_name}_en'] = translated_texts
    return df

@stub.local_entrypoint()
def main():
    # Test the translation function (can be removed in production)
    test_df = pd.DataFrame({
        'description': ['Esta es una descripción de prueba', 'Ceci est une description de test']
    })
    translated_df = translate_property_descriptions.remote(test_df, 'description')
    print(translated_df)
