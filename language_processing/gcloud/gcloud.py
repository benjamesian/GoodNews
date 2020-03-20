#!/usr/bin/env python3
from google.cloud import language_v1
from google.cloud.language_v1 import enums


def sample_analyze_sentiment(text_content):
    """
    Analyzing Sentiment in a String

    Args:
        text_content The text content to analyze
    """

    client = language_v1.LanguageServiceClient()

    # text_content = 'I am so happy and joyful.'

    # Available types: PLAIN_TEXT, HTML
    type_ = enums.Document.Type.PLAIN_TEXT

    # Optional. If not specified, the language is automatically detected.
    # For list of supported languages:
    # https://cloud.google.com/natural-language/docs/languages
    language = "en"
    document = {"content": text_content, "type": type_, "language": language}

    # Available values: NONE, UTF8, UTF16, UTF32
    encoding_type = enums.EncodingType.UTF8

    resp = client.analyze_sentiment(document, encoding_type=encoding_type)
    # Get overall sentiment of the input document
    print(f"Document sentiment score: {resp.document_sentiment.score}")
    print(f"Document sentiment magnitude: {resp.document_sentiment.magnitude}")

    # Get sentiment for all sentences in the document
    for sentence in resp.sentences:
        print(f"Sentence text: {sentence.text.content}")
        print(f"Sentence sentiment score: {sentence.sentiment.score}")
        print(f"Sentence sentiment magnitude: {sentence.sentiment.magnitude}")

    # Get the language of the text, which will be the same as
    # the language specified in the request or, if not specified,
    # the automatically-detected language.
    print(f"Language of the text: {resp.language}")


sample_analyze_sentiment("""
Now you can use the Natural Language API to analyze some text.
Run the following code to perform your first text sentiment analysis
""")
