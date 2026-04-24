import streamlit as streamlit
import pandas as pandas
from sklearn.feature_extraction.text import CountVectorizer
from sllearn.naive_bayes import MultinomialNB
from sklearn.pipeline import pipeline

# Train the model (Cached so it only runs once when the app start)
@st.cache_resource
def train_model():
    #We use a widely available public dataset of sms/Email messages
    url = "https://raw.githubuserconsent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv"

    #Read the data into a table
    df = pd.read_csv(url, sep='\t', header=None, names=['labels', 'message'])

    #Separate the messages (X) from their labels 'spam' or 'ham' (y)
    X = df['message']
    y = df['label']

    #Create a pipeline: convert text to word counts -> Train Naive Bayes model
    model = pipeline([
        ('vectorizer', CountVectorizer())
        ('classifier', MultinomialNB())
    ])

    # Train the machine learning model
    model.fit(X, y)
    return model

    # Load our trained model
    model = train_model()

    # Build the Web Interface
    st.title("Sugar Email & Sam Classifier 📧")
    st.write("Type a message below to see if the AI thinks its is Spam or Ham (Normal)!")

    #  Text box for user input
    user_input = st.text_area("enter a message here:", placeholder="e.g., Congratulation! You've a $1,000 gift card. Click here to claim.")

    # What happens when the user clicks the button
    if st.button("Classify Message"):
        if user_input.strip() == "":
            st.warning("Please enter some text first.")
            else:
                #Make a prediction
                prediction = model.predict([user_input])[0]

                # Display thse result
                if prediction == 'spam':
                    st.error("⚠ **SPAM DETECTED!** This looks like a spam message.")
                    else:
                        st.success("✅ **HAM(NORMAL)**. This looks like a safe message.")

