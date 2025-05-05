from openai import OpenAI
from mistralai import Mistral
from tqdm import tqdm
import dotenv
import os
import concurrent.futures
from typing import List
import requests
import time
import logging
import pandas as pd
from argparse import ArgumentParser
import json

END_OF_LINE = {"python": [], "java": [";"]}

dotenv.load_dotenv(override=True)


def filter_new_line(string):
    new_line_index = string.find("\n")
    if new_line_index == -1:
        return string
    else:
        return string[:new_line_index]


def deepseek_coder(prefix: str, suffix: str, max_tokens: int, temperature: float):
    try:
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API"),
            base_url="https://api.deepseek.com/beta/",
        )

        response = client.completions.create(
            model="deepseek-chat",
            prompt=prefix,
            suffix=suffix,
            max_tokens=max_tokens,
            temperature=temperature,
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


def codestral_latest(prefix: str, suffix: str, max_tokens: int, temperature: float):
    try:
        time.sleep(1.5)
        body = {
            "prompt": prefix,
            "suffix": suffix,
            "model": "codestral-latest",
            "max_tokens": max_tokens,
            "temperature": temperature,
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
        return filter_new_line(code)
    except Exception as e:
        logging.error(e)
        return None


def gpt(prefix: str, suffix: str, max_tokens: int, temperature: float):
    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API"),
        )

        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prefix,
            suffix=suffix,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        code = response.choices[0].text
        if not code:
            return ""
        return filter_new_line(code)
    except Exception as e:
        logging.error(e)
        return None
    
def get_response(prefix: str, suffix: str, model: str, max_tokens: int, temperature: float):
    match model:
        case "deepseek-coder" | "deepseek-chat":
            return deepseek_coder(prefix, suffix, max_tokens, temperature)
        case "gpt-3.5-turbo-instruct":
            return gpt(prefix, suffix, max_tokens, temperature)
        case "codestral-latest":
            return codestral_latest(prefix, suffix, max_tokens, temperature)
        case _:
            raise NotImplementedError(f"Model {model} not implemented")
        


def prompt(prefixes: List[str], suffixes: List[str], model: str, max_tokens: int, temperature: float, worker: int):
    responses = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=worker) as executor:
        futures = {
            executor.submit(get_response, prefix, suffix, model, max_tokens, temperature): idx
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


def main(args):
    df = pd.read_json(args.input, lines=True)
    if args.debug:
        df = df.head(10)
    prefixes = []
    suffixes = []
    for _, row in df.iterrows():
        builder_output = json.loads(row["builder_output_refine"])    # builder_output = json.loads(row["builder_output"])
        prefixes.append(builder_output["prefix"])
        suffixes.append(builder_output["suffix"])

    completions = prompt(prefixes, suffixes, args.model, args.max_tokens, args.temperature, args.worker)  
    df["completion_refine"] = completions   # df["completions"] = completions
    df.to_json(args.output, orient="records", lines=True)

     
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--temperature", type=float, default=0.01)
    parser.add_argument("--worker", type=int, default=3)
    parser.add_argument("--debug", action="store_true", default=False)
    args = parser.parse_args()
    main(args)
    

