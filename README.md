# Email & SMS Spam Classifier 📧

A simple machine learning web application that classifies incoming messages as either Spam or Ham (normal). 

This project uses a Natural Language Processing (NLP) model trained on a public dataset of SMS and email messages to detect spam patterns based on word frequencies.

## Technologies Used
* Python: The core programming language.
* Streamlit: Used to build the interactive web interface and handle deployment.
* Scikit-learn: Used for the machine learning pipeline (CountVectorizer and Multinomial Naive Bayes).
* Pandas: Used for data manipulation and reading the dataset.

## How It Works
1. The app downloads a dataset of labeled messages.
2. It converts the text data into a numerical format using a Bag-of-Words approach.
3. A Naive Bayes classifier is trained on the data.
4. The user enters a custom message into the web interface, and the model predicts its classification in real-time.

## Deployment
This application is designed to be easily deployed using Streamlit Community Cloud. Simply link this repository to Streamlit, and it will automatically install the dependencies listed in requirements.txt and launch the app.
