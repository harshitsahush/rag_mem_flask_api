from flask import Flask, request, render_template, redirect, jsonify, session
from flask_session import Session
from utils import *
import os.path
import shutil



#to reset flask session, simply delete flask session folder
path = "./flask_session"

if(os.path.isdir(path)):
    shutil.rmtree(path)



app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/" , methods = ["GET", "POST"])
def test1():
    return redirect("/process_pdf")

@app.route("/process_pdf", methods = ["GET", "POST"])
def test2():
    if(request.method == "POST"):
        pdfs = request.files['pdf_file']
        text = process_files(pdfs)

        #set session varibale to show that file has been processed
        session['file_processed'] = True

        #redirect to process_query
        return redirect("/process_query")

    else:
        return render_template("process_pdf.html")


@app.route("/process_query", methods=["GET", "POST"])
def test3():
    if(request.method == "POST"):
        #if file_processed not set,show option to redirect to process_pdf page
        if('file_processed' not in session):
            return """You have not processed a file yet.<a href = "/process_pdf">Click here</a> to go to the pdf upload page."""
        
        else:
            #if reset checkbox is selected, reset the chat memory session var
            if(request.form.get("reset_history")):
                if("chat_history" in session):
                    session.pop('chat_history', None)
            
            print("chat_history" in session)

            query = request.form['query']
            if("chat_history" in session):
                query = contextualize(query, session['chat_history'])

            sim_docs = sim_search(query)
            query_response = generate_response(query, sim_docs)

            if("chat_history" in session):
                new_chat_history = generate_chat_history(session["chat_history"], query, query_response)
            else:
                new_chat_history = generate_chat_history("", query, query_response)
            session["chat_history"] = new_chat_history

            return render_template("process_query.html", res = query_response)
    else:
        return render_template("process_query.html")

if(__name__ == "__main__"):
    app.run(debug = True)