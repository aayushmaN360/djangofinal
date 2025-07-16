# create_new_model.py
import pickle
import numpy as np

# Minimal valid model structure
artifacts = {
    'vocab': ['hello', 'world', 'test'],
    'word2idx': {'hello': 0, 'world': 1, 'test': 2},
    'priors': {'safe': 0.7, 'toxic': 0.3},
    'likelihoods': {
        'safe': np.log(np.array([0.4, 0.3, 0.3])),
        'toxic': np.log(np.array([0.1, 0.1, 0.8]))
    },
    'total_words_per_class': {'safe': 100, 'toxic': 50},
    'alpha': 1,
    'V': 3,
    'classes': ['safe', 'toxic']
}

with open('blog/naive_bayes_toxicity_model.pkl', 'wb') as f:
    pickle.dump(artifacts, f, protocol=pickle.HIGHEST_PROTOCOL)

print("Created new minimal model file at blog/naive_bayes_toxicity_model.pkl")