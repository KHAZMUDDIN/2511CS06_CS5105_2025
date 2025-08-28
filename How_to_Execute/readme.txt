# How to Execute tut01.py

## 1. Clone the Repository
Download or clone this repository:
    git clone <your_repo_link>
    cd How_to_Execute

## 2. Create Virtual Environment (optional but recommended)
    python -m venv venv
    source venv/bin/activate   # On Linux/Mac
    venv\Scripts\activate      # On Windows

## 3. Install Dependencies
    pip install -r requirements.txt

## 4. Run the Streamlit App
    streamlit run tut01.py

This will start a local server. Open the link shown in your terminal (usually http://localhost:8501).

## 5. Sample Input
Use the file `sample_input.csv` (or .xlsx/.txt) provided in this folder as input for testing.

## 6. Make the App Live (on Streamlit Cloud)
1. Push this folder to your GitHub repository.
2. Go to https://share.streamlit.io/
3. Sign in with GitHub and select your repository.
4. Choose the `How_to_Execute/tut01.py` file as the main app file.
5. Deploy 🚀

Your app will now be live with a public link.

