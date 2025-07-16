import pickle
import numpy as np

def repair_model(input_path, output_path):
    try:
        print(f"Attempting to repair {input_path}")
        with open(input_path, 'rb') as f:
            data = pickle.load(f)
            
        print("Original data keys:", list(data.keys()))
        
        # Fix common issues
        repaired = False
        
        # 1. Convert likelihood arrays to numpy if needed
        if 'likelihoods' in data and isinstance(data['likelihoods'], dict):
            for cls in data['likelihoods']:
                if isinstance(data['likelihoods'][cls], list):
                    data['likelihoods'][cls] = np.array(data['likelihoods'][cls])
                    repaired = True
        
        # 2. Ensure word2idx is properly formatted
        if 'word2idx' in data and not isinstance(data['word2idx'], dict):
            if hasattr(data['word2idx'], 'to_dict'):
                data['word2idx'] = data['word2idx'].to_dict()
                repaired = True
        
        # 3. Convert pandas Series to dict if needed
        if 'priors' in data and not isinstance(data['priors'], dict):
            if hasattr(data['priors'], 'to_dict'):
                data['priors'] = data['priors'].to_dict()
                repaired = True
        
        # 4. Fill in missing values with defaults
        if 'alpha' not in data:
            data['alpha'] = 1
            repaired = True
            
        if 'V' not in data:
            data['V'] = len(data.get('vocab', []))
            repaired = True
            
        # Save repaired version
        with open(output_path, 'wb') as f:
            pickle.dump(data, f, protocol=4)
            
        print(f"Repaired model saved to {output_path}")
        print(f"Repairs performed: {repaired}")
        
        return repaired
        
    except Exception as e:
        print(f"Repair failed: {e}")
        return False

if __name__ == "__main__":
    input_path = "blog/naive_bayes_toxicity_model.pkl"
    output_path = "blog/repaired_model.pkl"
    
    if repair_model(input_path, output_path):
        print("\nNext steps:")
        print("1. Update ai_toxicity.py to use the repaired model:")
        print("   toxicity_detector = ToxicityDetector('blog/repaired_model.pkl')")
        print("2. Re-run the verification script: python verify_model.py")
    else:
        print("Repair unsuccessful. Consider retraining your model.")