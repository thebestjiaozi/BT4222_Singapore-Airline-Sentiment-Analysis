import pandas as pd
import numpy as np
from scipy.sparse import load_npz
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, f1_score

X_train = load_npz("X_train_tfidf.npz")
X_val   = load_npz("X_val_tfidf.npz")
X_test  = load_npz("X_test_tfidf.npz")

y_train = pd.read_csv("train_split.csv")['label']
y_val   = pd.read_csv("val_split.csv")['label']
y_test  = pd.read_csv("test_split.csv")['label']

X_train_full = np.vstack([X_train.toarray(), X_val.toarray()])
y_train_full = pd.concat([y_train, y_val], ignore_index=True)

# Build Logistic Regression Baseline
model = LogisticRegression(
    max_iter=1000,
    solver='liblinear',      
    C=1.0,                  
    class_weight='balanced' 
)

model.fit(X_train, y_train)

#Evaluate on validation and test sets
for name, X, y in [('Validation', X_val, y_val), ('Test', X_test, y_test)]:
    y_pred = model.predict(X)
    print(f"\n{name} Set Performance:")
    print("Accuracy:", accuracy_score(y, y_pred))
    print("F1-score:", f1_score(y, y_pred, average='weighted'))
    print(classification_report(y, y_pred))
