# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 23:42:11 2025

@author: 15857
"""
   
import pandas as pd
from tqdm import tqdm
import re
import argparse

def compute_text_concreteness(text, unigram_dict, bigram_dict):
    """
    Given a text (string), tokenizes it and computes the average concreteness.

    For each text:
      - If the text is not a valid string, return -1.
      - Remove punctuation.
      - Remove numeric characters.
      - Strip extra whitespace.
      - Convert to lowercase and split on whitespace.
      - For each token position, check if a two-word bigram exists in bigram_dict.
        If yes, add that rating and skip the next token.
      - Otherwise, if the individual token exists in unigram_dict, add its rating.
    Returns the average rating (arithmetic mean) or -1 if no rating was found.
    """
    if not isinstance(text, str):
        return -1

    # Remove punctuation and numeric characters, then strip whitespace.
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text).strip()

    if not text:
        return -1

    tokens = text.lower().split()
    ratings = []
    i = 0
    while i < len(tokens):
        # Check for bigram match if possible.
        if i < len(tokens) - 1:
            candidate_bigram = tokens[i] + " " + tokens[i+1]
            if candidate_bigram in bigram_dict:
                ratings.append(bigram_dict[candidate_bigram])
                i += 2
                continue
        # Check for unigram match.
        token = tokens[i]
        if token in unigram_dict:
            ratings.append(unigram_dict[token])
        i += 1

    return sum(ratings) / len(ratings) if ratings else -1

def process_text_data(text_data_csv, concreteness_csv, text_fields, output_csv):
    """
    Processes a CSV file containing text data to compute concreteness scores for specified text fields.

    Parameters:
      - text_data_csv: CSV file path with the text data.
      - concreteness_csv: CSV file path containing concreteness ratings.
        The concreteness CSV should have columns:
          - "Word": string (a unigram or a bigram as two words separated by a space)
          - "Conc.M": numeric rating
          - "Bigram": flag (1 for bigrams, 0 for unigrams)
      - text_fields: List of column names in the text data to process.
      - output_csv: The output CSV file path for the processed data.

    For each provided text field that exists in the input CSV, the function:
      - Computes the average concreteness (using bigrams when available, then unigrams).
      - Stores the computed average in a new column named "avg_conc_<field>".
    """
    # Load text data.
    text_df = pd.read_csv(text_data_csv, dtype=str)
    
    # Load concreteness ratings.
    conc_df = pd.read_csv(concreteness_csv, dtype={"Word": str, "Conc.M": float, "Bigram": int})
    conc_df = conc_df.dropna(subset=["Word"])
    conc_df["Word"] = conc_df["Word"].astype(str).str.lower()

    # Build dictionaries for unigrams and bigrams.
    unigram_dict = {}
    bigram_dict = {}
    for _, row in conc_df.iterrows():
        word = row["Word"].strip()
        rating = row["Conc.M"]
        if row["Bigram"] == 1:
            bigram_dict[word] = rating
        else:
            unigram_dict[word] = rating

    # Process each specified text field.
    for field in text_fields:
        if field in text_df.columns:
            concreteness_scores = []
            for _, row in tqdm(text_df.iterrows(), total=len(text_df), desc=f"Processing {field}"):
                text = row[field]
                avg_rating = compute_text_concreteness(text, unigram_dict, bigram_dict)
                concreteness_scores.append(avg_rating)
            text_df[f"avg_conc_{field}"] = concreteness_scores
        else:
            print(f"Warning: Field '{field}' not found in the data.")

    # Save the processed data to the output CSV.
    text_df.to_csv(output_csv, index=False)
    print(f"Processing complete. Results saved to '{output_csv}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute concreteness scores for specified text fields in a CSV file.")
    parser.add_argument("--text_data_csv", type=str, default="data.csv", 
                        help="Path to the CSV file containing text data.")
    parser.add_argument("--concreteness_csv", type=str, default="concretenessRatings.csv", 
                        help="Path to the CSV file with concreteness ratings.")
    parser.add_argument("--fields", type=str, nargs="+", 
                        default=["headline", "abstract", "snippet", "lead_paragraph"],
                        help="List of text field names to process.")
    parser.add_argument("--output_csv", type=str, default="output.csv", 
                        help="Path for the output CSV file with concreteness scores.")
    args = parser.parse_args()

    process_text_data(args.text_data_csv, args.concreteness_csv, args.fields, args.output_csv)
