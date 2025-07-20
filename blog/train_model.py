import pandas as pd
import numpy as np
import re
import pickle
from collections import Counter
import os

print("--- Starting Local Model Training Process ---")

# ==============================================================================
#  STEP 1: DEFINE FILE PATHS AND LOAD DATA
# ==============================================================================
# This script assumes it is located in the 'blog' app directory.

# Get the directory where this script is located (i.e., the 'blog' folder)
script_dir = os.path.dirname(__file__)

# Define the full path to the dataset and the output model file
DATASET_PATH = os.path.join(script_dir, 'balanced_3class_toxic_dataset.csv')
OUTPUT_MODEL_PATH = os.path.join(script_dir, 'naive_bayes_model.pkl')

print(f"\nAttempting to load dataset from: {DATASET_PATH}")

try:
    df = pd.read_csv(DATASET_PATH)
    print(f"Successfully loaded dataset with {len(df)} rows.")
except FileNotFoundError:
    print(f"\n!!! ERROR: Dataset not found at the expected location.")
    print("Please make sure 'balanced_3class_toxic_dataset.csv' is inside your 'blog' app folder.")
    exit() # Stop the script if the data isn't found
except Exception as e:
    print(f"\n!!! ERROR: Could not read the CSV file. Please check for formatting errors. Details: {e}")
    exit()

# ==============================================================================
#  STEP 2: RUN THE ENTIRE TRAINING & EVALUATION PROCESS
# ==============================================================================
# This is the same robust training and evaluation logic from the Colab script.

# --- 2a. Define Preprocessing Functions ---
stop_words = {
    'i','me','my','myself','we','our','ours','ourselves','you','your','yours','yourself',
    'yourselves','he','him','his','himself','she','her','hers','herself','it','its','itself',
    'they','them','their','theirs','themselves','what','which','who','whom','this','that','these',
    'those','am','is','are','was','were','be','been','being','have','has','had','having','do',
    'does','did','doing','a','an','the','and','but','if','or','because','as','until','while','of',
    'at','by','for','with','about','against','between','into','through','during','before','after',
    'above','below','to','from','up','down','in','out','on','off','over','under','again','further',
    'then','once','here','there','when','where','why','how','all','any','both','each','few','more',
    'most','other','some','such','no','nor','not','only','own','same','so','than','too','very',
    'can','will','just','don','should','now'
}

def stem(word):
    suffixes = ['ing', 'ly', 'ed', 's', 'es']
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[:-len(suffix)]
    return word

def preprocess(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', '', text)
    tokens = text.split()
    return [stem(word) for word in tokens if word not in stop_words]

# --- 2b. Prepare Data ---
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
split_idx = int(0.8 * len(df))
train_df, test_df = df.iloc[:split_idx], df.iloc[split_idx:]

X_train, y_train = train_df['comment_text'].tolist(), train_df['label'].tolist()
X_test, y_test = test_df['comment_text'].tolist(), test_df['label'].tolist()
print("Data loaded and split successfully.")

# --- 2c. Build Vocabulary and Train the Model ---
print("Building vocabulary...")
vocab = set()
for text in X_train:
    vocab.update(preprocess(text))
vocab = sorted(list(vocab))
word2idx = {word: i for i, word in enumerate(vocab)}

print("Training Naive Bayes model...")
classes = sorted(list(set(y_train)))
class_counts = Counter(y_train)
priors = {c: np.log(class_counts[c] / len(y_train)) for c in classes}

alpha = 1
word_counts_per_class = {c: np.ones(len(vocab)) * alpha for c in classes}
total_words_per_class = {c: len(vocab) * alpha for c in classes}

for text, label in zip(X_train, y_train):
    tokens = preprocess(text)
    for word in tokens:
        if word in word2idx:
            word_counts_per_class[label][word2idx[word]] += 1
            total_words_per_class[label] += 1

likelihoods = {c: np.log(word_counts_per_class[c] / total_words_per_class[c]) for c in classes}
print("Model training complete.")

# --- 2d. Evaluate the Model (with Full Classification Report) ---
def predict(text):
    tokens = preprocess(text)
    class_scores = {c: priors[c] for c in classes}
    for word in tokens:
        for c in classes:
            if word in word2idx:
                class_scores[c] += likelihoods[c][word2idx[word]]
            else:
                class_scores[c] += np.log(alpha / total_words_per_class[c])
    return max(class_scores, key=class_scores.get)

print("\nEVALUATING MODEL ON TEST SET...")
y_pred = [predict(text) for text in X_test]

conf_matrix = {true_class: {pred_class: 0 for pred_class in classes} for true_class in classes}
for true_label, pred_label in zip(y_test, y_pred):
    conf_matrix[true_label][pred_label] += 1

print("\n--- Confusion Matrix ---")
header = f"{'Actual ↓ | Predicted →':<20}" + " | ".join([f"{c:<15}" for c in classes])
print(header)
print("-" * len(header))
for true_class in classes:
    row = [str(conf_matrix[true_class][pred_class]) for pred_class in classes]
    print(f"{true_class:<20}" + " | ".join([f"{r:<15}" for r in row]))

def safe_divide(numerator, denominator): return numerator / denominator if denominator != 0 else 0

metrics = {}
for c in classes:
    TP = conf_matrix[c][c]
    FP = sum(conf_matrix[other_class][c] for other_class in classes if other_class != c)
    FN = sum(conf_matrix[c][other_class] for other_class in classes if other_class != c)
    precision = safe_divide(TP, TP + FP)
    recall = safe_divide(TP, TP + FN)
    f1_score = safe_divide(2 * precision * recall, precision + recall)
    metrics[c] = {'precision': precision, 'recall': recall, 'f1-score': f1_score}

print("\n--- Classification Report ---")
print(f"{'Class':<20}{'Precision':<15}{'Recall':<15}{'F1-Score':<15}")
print("---------------------------------------------------------------")
for c in classes:
    m = metrics[c]
    print(f"{c:<20}{m['precision']:.4f}{m['recall']:<15.4f}{m['f1-score']:.4f}")
print("---------------------------------------------------------------")

total_correct = sum(conf_matrix[c][c] for c in classes)
total_samples = len(y_test)
accuracy = safe_divide(total_correct, total_samples)
print(f"\nOverall Accuracy: {accuracy:.4f} ({total_correct} out of {total_samples} correct)")

# --- 3. Save the Final Model Artifacts ---
model_artifacts = {
    "word2idx": word2idx, "classes": classes, "priors": priors,
    "likelihoods": likelihoods, "total_words_per_class": total_words_per_class,
    "alpha": alpha, "stop_words": stop_words, "non_toxic_label": 'non-toxic'
}

with open(OUTPUT_MODEL_PATH, "wb") as f:
    pickle.dump(model_artifacts, f)

print(f"\n✅ Model trained and saved successfully to '{OUTPUT_MODEL_PATH}'")