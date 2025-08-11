import streamlit as st

def main():
    st.title("Form Agent")
    st.write("This is my first deployed Streamlit app!")
    
    name = st.text_input("Enter your name:")
    if st.button("Submit"):
        st.success(f"Hello, {name}!")

if __name__ == "__main__":
    main()
