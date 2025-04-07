from openai import OpenAI
from tqdm import tqdm
import dotenv
import os
import concurrent.futures
from typing import List
import requests
import time
import logging

END_OF_LINE = {"python": [], "java": [";"]}

dotenv.load_dotenv(override=True)


def filter_new_line(string):
    new_line_index = string.find("\n")
    if new_line_index == -1:
        return string
    else:
        return string[:new_line_index]


def deepseek_coder(prefix: str, suffix: str):
    try:
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API"),
            base_url="https://api.deepseek.com/beta/",
        )

        response = client.completions.create(
            model="deepseek-coder",
            prompt=prefix,
            suffix=suffix,
            max_tokens=2048,
            temperature=0.01,
            stop=[
                "<｜fim▁begin｜>",
                "<｜fim▁hole｜>",
                "<｜fim▁end｜>",
                "//",
                "<｜end▁of▁sentence｜>",
                "\n\n",
                "\r\n\r\n",
                "/src/",
                "#- coding: utf-8",
                "```",
                "\nclass",
                "\nfunction",
            ],
        )
        code = response.choices[0].text
        if not code:
            return ""
        return filter_new_line(code)
    except Exception as e:
        logging.error(e)
        return None


def costral_latest(prefix: str, suffix: str):
    try:
        time.sleep(0.5)
        body = {
            "prompt": prefix,
            "suffix": suffix,
            "model": "codestral-latest",
            "max_tokens": 2048,
            "temperature": 0.01,
            "stop": [
                "[PREFIX]",
                "[SUFFIX]",
                "\n\n",
                "\r\n\r\n",
                "/src/",
                "#- coding: utf-8",
                "```",
                "\nclass",
                "\nfunction",
            ],
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {os.getenv('CODESTRAL_API')}",
        }
        url = "https://codestral.mistral.ai/v1/fim/completions"
        response = requests.post(url=url, json=body, headers=headers)
        code = response.json()["choices"][0]["message"]["content"]
        if not code:
            return ""
        return filter_new_line(code)
    except Exception as e:
        logging.error(e)
        return None

    
def get_response(prefix: str, suffix: str, model: str):
    match model:
        case "deepseek-coder":
            return deepseek_coder(prefix, suffix)
        case "codestral-latest":
            return costral_latest(prefix, suffix)
        case _:
            raise NotImplementedError(f"Model {model} not implemented")

def prompt(prefixes: List[str], suffixes: List[str], model: str):
    responses = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(get_response, prefix, suffix, model): idx
            for idx, (prefix, suffix) in enumerate(zip(prefixes, suffixes))
        }
        for future in tqdm(
            concurrent.futures.as_completed(futures), total=len(futures)
        ):
            idx = futures[future]
            code = future.result()
            logging.info(idx)
            logging.info(code)
            logging.info("=" * 100)
            responses[idx] = code
    responses = [responses[idx] for idx in range(len(responses))]
    return responses
