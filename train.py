import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report, confusion_matrix

df = pd.read_csv('intents.csv')
X_train, X_test, y_train, y_test = train_test_split(df['question'], df['category'], test_size=0.2, random_state=42, stratify=df['category'])

model = make_pipeline(TfidfVectorizer(), MultinomialNB())
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("--- Accuracy & Evaluation ---")
print(classification_report(y_test, y_pred))
print("--- Confusion Matrix ---")
print(confusion_matrix(y_test, y_pred))

joblib.dump(model, 'model.pkl')
print("Model saved to model.pkl")
