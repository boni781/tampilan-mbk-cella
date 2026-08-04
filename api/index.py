from flask import Flask

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

@app.route("/")
def home():
    return "<h1>Dashboard Monitoring Sertifikasi</h1>"

# Penting untuk Vercel
app = app

# Agar bisa dijalankan lokal
if __name__ == "__main__":
    app.run(debug=True)