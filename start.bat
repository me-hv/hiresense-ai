call .\venv\Scripts\activate.bat
pip install -r requirements.txt
python -m spacy download en_core_web_sm
streamlit run src\ui\app.py
