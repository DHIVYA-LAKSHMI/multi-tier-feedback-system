from flask import Flask, request, render_template
import pymysql
import boto3

app = Flask(__name__)

# DB1 (Raw Feedback)
DB1_CONFIG = {
    'host': 'db1 endpoint',
    'user': 'admin',
    'password': 'your credentials',
    'database': 'your credentials'
}

# DB2 (Analyzed Feedback)
DB2_CONFIG = {
    'host': 'db2 endpoint 2',
    'user': 'admin',
    'password': 'your credentials',
    'database': 'your credentials'
}

# Initialize Amazon Comprehend client
comprehend = boto3.client('comprehend', region_name='us-east-2')

def get_db_connection(db_config):
    return pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )

@app.route('/', methods=['GET'])
def feedback_form():
    return render_template('index.html')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    feedback_text = request.form.get('feedback', '').strip()
    print("📝 Feedback received:", feedback_text)

    if not feedback_text:
        return "Feedback cannot be empty.", 400

    # Save raw feedback into DB1
    try:
        conn1 = get_db_connection(DB1_CONFIG)
        with conn1.cursor() as cursor:
            cursor.execute("INSERT INTO feedback (comment) VALUES (%s)", (feedback_text,))
        conn1.commit()
        conn1.close()
        print("✅ Raw feedback saved to DB1.")
    except Exception as e:
        return f"❌ DB1 Insert Error: {str(e)}", 500

    # Analyze sentiment using Comprehend
    try:
        sentiment_response = comprehend.detect_sentiment(Text=feedback_text, LanguageCode='en')
        sentiment = sentiment_response.get('Sentiment', 'NEUTRAL')
        scores = sentiment_response.get('SentimentScore', {})
        print("🔍 Sentiment:", sentiment, "| Scores:", scores)
    except Exception as e:
        print(f"❌ Comprehend error: {str(e)}")
        sentiment = 'NEUTRAL'
        scores = {
            'Positive': 0.0,
            'Negative': 0.0,
            'Neutral': 1.0,
            'Mixed': 0.0
        }

    # Save analyzed feedback into DB2
    try:
        conn2 = get_db_connection(DB2_CONFIG)
        with conn2.cursor() as cursor:
            cursor.execute(
                "INSERT INTO analysis (sentiment, key_phrases) VALUES (%s, %s)",
                (sentiment, '')  # key_phrases empty for now
            )
        conn2.commit()
        conn2.close()
        print("✅ Sentiment saved to DB2.")
    except Exception as e:
        return f"❌ DB2 Insert Error: {str(e)}", 500

    # Format scores for frontend display
    formatted_scores = {k: f"{v:.2f}" for k, v in scores.items()}

    # Render template with sentiment and scores
    return render_template('index.html', sentiment=sentiment, scores=formatted_scores)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
