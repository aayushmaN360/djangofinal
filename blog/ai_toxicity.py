import pickle
import numpy as np
import re
from collections import Counter
from django.conf import settings
import os

class ToxicityClassifier:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(settings.BASE_DIR, 'blog', 'naive_bayes_model.pkl')
        
        # This is the ONLY label we consider non-toxic. Everything else is a flag.
        self.NON_TOXIC_LABEL = 'non-toxic'

        try:
            with open(model_path, 'rb') as f:
                artifacts = pickle.load(f)
            
            self.priors = artifacts['priors']
            self.likelihoods = artifacts['likelihoods']
            self.word2idx = artifacts['word2idx']
            self.classes = artifacts['classes']
            self.alpha = artifacts['alpha']
            self.V = artifacts['V']
            self.total_words_per_class = artifacts['total_words_per_class']
            print("Toxicity model loaded successfully from __init__.")
            self.model_loaded = True
        except FileNotFoundError:
            print(f"Error: Model file not found at {model_path}. Predictions will be disabled.")
            self.model_loaded = False
            self.priors = None

    def _preprocess(self, text):
        text = str(text).lower()
        text = re.sub(r'[^a-z\s]', '', text)
        return text.split()

    def predict(self, text):
        """
        Predicts if a text is toxic based on its predicted label.
        Returns a tuple: (is_toxic: bool, predicted_label: str)
        """
        if not self.model_loaded:
            return False, 'clean' # Failsafe if model isn't loaded

        tokens = self._preprocess(text)
        counts = Counter(tokens)
        class_scores = {}
        
        for c in self.classes:
            score = np.log(self.priors[c])
            for word, count in counts.items():
                if word in self.word2idx:
                    idx = self.word2idx[word]
                    score += self.likelihoods[c][idx] * count
                else:
                    score += np.log(self.alpha / (self.total_words_per_class[c] + self.alpha * self.V)) * count
            class_scores[c] = score
        
        predicted_label = max(class_scores, key=class_scores.get)
        
        # --- NEW, SIMPLER LOGIC ---
        # If the label is NOT 'non-toxic', then it IS toxic.
        is_toxic = predicted_label != self.NON_TOXIC_LABEL
        
        return is_toxic, predicted_label

# Create a single, shared instance for the whole app
toxicity_classifier = ToxicityClassifier()