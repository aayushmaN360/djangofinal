import pickle
import os
from pathlib import Path

# Get the absolute path to the model file
model_path = Path(__file__).parent / 'blog' / 'naive_bayes_toxicity_model.pkl'

print(f"Verifying model at: {model_path}")
print(f"File size: {model_path.stat().st_size} bytes")

try:
    with open(model_path, 'rb') as f:
        data = pickle.load(f)
        print("✅ Successfully loaded pickle file!")
        print("Keys in pickle file:", list(data.keys()))
        
        # Check basic structure
        required_keys = ['vocab', 'word2idx', 'priors', 'likelihoods', 
                         'total_words_per_class', 'alpha', 'V', 'classes']
        for key in required_keys:
            if key in data:
                print(f"✅ {key}: {type(data[key])}")
            else:
                print(f"❌ Missing key: {key}")
                
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("\nTroubleshooting steps:")
    print("1. Verify the file is a valid pickle file")
    print("2. Check if the file was corrupted during download")
    print("3. Re-run the training script to generate a new model")
    print("4. Try opening the file in binary mode and re-saving it:")
    print("   import pickle")
    print("   with open('blog/naive_bayes_toxicity_model.pkl', 'wb') as f:")
    print("       pickle.dump(artifacts, f, protocol=pickle.HIGHEST_PROTOCOL)")