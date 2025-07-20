import pickle
import numpy as np
import re
from collections import Counter
from django.conf import settings
import os

class ToxicityClassifier:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), 'naive_bayes_model.pkl')
        
        self.NON_TOXIC_LABEL = 'non-toxic'
        self.model_loaded = False

        try:
            with open(model_path, 'rb') as f:
                artifacts = pickle.load(f)
            
            self.priors = artifacts['priors']
            self.likelihoods = artifacts['likelihoods']
            self.word2idx = artifacts['word2idx']
            self.classes = artifacts['classes']
            self.alpha = artifacts['alpha']
            self.total_words_per_class = artifacts['total_words_per_class']
            self.stop_words = artifacts['stop_words']

            self.model_loaded = True
            print("Toxicity model loaded successfully.")
        except FileNotFoundError:
            print(f"ERROR: Model file not found at {model_path}. Predictions will be disabled.")
        except Exception as e:
            print(f"ERROR: An unexpected error occurred while loading the model: {e}")

    def stem(self, word):
        suffixes = ['ing', 'ly', 'ed', 's', 'es']
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        return word

    def preprocess(self, text):
        text = str(text).lower()
        text = re.sub(r'[^a-z\s]', '', text)
        tokens = text.split()
        return [self.stem(w) for w in tokens if w not in self.stop_words]

    def predict(self, text):
        if not self.model_loaded:
            return False, 'clean'

        tokens = self.preprocess(text)
        
        # --- START OF NEW, MORE INTELLIGENT LOGIC ---

        # 1. Calculate the log scores for each class (same as before)
        class_scores = {c: self.priors[c] for c in self.classes}
        for word in tokens:
            for c in self.classes:
                if word in self.word2idx:
                    class_scores[c] += self.likelihoods[c][self.word2idx[word]]
                else:
                    class_scores[c] += np.log(self.alpha / self.total_words_per_class[c])
        
        # 2. Convert the raw log scores into probabilities (0 to 1)
        # This is a simplified version of the "softmax" function
        scores = np.array(list(class_scores.values()))
        exp_scores = np.exp(scores - np.max(scores)) # Subtract max for numerical stability
        probabilities = exp_scores / exp_scores.sum()
        class_probabilities = {c: p for c, p in zip(self.classes, probabilities)}

        # 3. Apply a threshold to make a final decision
        # THIS IS YOUR NEW TUNING KNOB!
        # 0.70 means we only flag if we are >70% sure it's toxic.
        TOXICITY_THRESHOLD = 0.70 
        
        is_toxic = False
        final_label = 'clean'
        highest_toxic_prob = 0
        
        # Find the total probability of all toxic classes
        total_toxic_prob = sum(prob for label, prob in class_probabilities.items() if label != self.NON_TOXIC_LABEL)

        if total_toxic_prob > TOXICITY_THRESHOLD:
            is_toxic = True
            # Find which toxic class was the most likely
            toxic_classes = {label: prob for label, prob in class_probabilities.items() if label != self.NON_TOXIC_LABEL}
            final_label = max(toxic_classes, key=toxic_classes.get)

        # --- END OF NEW LOGIC ---

        return is_toxic, final_label

# Singleton Instance
toxicity_classifier = ToxicityClassifier()