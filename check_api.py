import streamlit as st

def check_api_key():
    """
    Checks for the presence and length of the GEMINI_API_KEY from st.secrets.
    """
    st.title("API Key Status Check")
    st.write("This simple app checks if Streamlit can successfully load the API key from `.streamlit/secrets.toml`.")
    st.divider()

    try:
        # Streamlit automatically looks for the key under the 'GEMINI_API_KEY'
        # section in the secrets.toml file.
        api_key = st.secrets["GEMINI_API_KEY"]

        # Check if the key is not empty and has a reasonable length (Gemini keys are long)
        if api_key and len(api_key) > 30:
            st.success("✅ Success! The **GEMINI_API_KEY** was loaded correctly.")
            st.code(f"Key length: {len(api_key)} characters")
            st.info("Now you can try running your main app again (`streamlit run app.py`).")
        else:
            # This path is hit if the key is found, but it's too short (maybe a placeholder)
            st.error("❌ Key Found, but Invalid Format!")
            st.warning("The key loaded is too short or empty. Please check your `.streamlit/secrets.toml` file.")

    except KeyError:
        # This is the most common error: the key wasn't found in the secrets file
        st.error("🛑 Error: API Key Not Found (KeyError)")
        st.write("Streamlit could not find the key named **GEMINI_API_KEY** in the `st.secrets` dictionary.")
        st.markdown(
            """
            **Action Required:**
            1.  Ensure you have a directory named **`.streamlit`** in your project folder.
            2.  Ensure you have a file named **`secrets.toml`** inside the `.streamlit` directory.
            3.  Ensure the file contains the key in the correct format:
                ```toml
                GEMINI_API_KEY="AIzaSy...your-39-character-key-here"
                ```
            """
        )
    except Exception as e:
        # Catch any other unexpected loading errors
        st.exception(e)
        st.error("An unexpected error occurred while loading the key.")

if __name__ == "__main__":
    check_api_key()