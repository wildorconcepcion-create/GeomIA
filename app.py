from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import flash
from flask import url_for
from flask import abort
import requests

from flask_login import LoginManager
from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required
from flask_login import current_user

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from models import db, Usuario, Evento

app = Flask(__name__)

app.config["SECRET_KEY"] = "geomia-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///geomia.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

ADMIN_EMAILS = [
    "wildor@gmail.com"
]

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


with app.app_context():
    db.create_all()


# =====================================
# INICIO
# =====================================

@app.route("/")
def home():
    return redirect(url_for("login"))



##importar eventos reales de satelite


@app.route("/importar-nasa")
@login_required
def importar_nasa():

    if current_user.rol != "administrador":
        abort(403)

    url = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=20"

    response = requests.get(url)

    datos = response.json()

    for evento_nasa in datos["events"]:

        existe = Evento.query.filter_by(
            nombre_evento=evento_nasa["title"]
        ).first()

        if not existe:

            evento = Evento(
                nombre_evento=evento_nasa["title"],
                tipo_evento=evento_nasa["categories"][0]["title"],
                fecha=evento_nasa["geometry"][0]["date"][:10],
                ubicacion="NASA EONET",
                descripcion="Evento importado desde NASA",
                nivel_riesgo="MEDIO"
            )

            db.session.add(evento)

    db.session.commit()

    flash("Eventos importados desde NASA")

    return redirect(url_for("eventos"))
# =====================================
# REGISTRO
# =====================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        nombre = request.form["nombre"]
        correo = request.form["correo"]
        password = request.form["password"]

        usuario_existente = Usuario.query.filter_by(
            correo=correo
        ).first()

        if usuario_existente:
            flash("El correo ya se encuentra registrado")
            return redirect(url_for("register"))

        if correo in ADMIN_EMAILS:
            rol = "administrador"
        else:
            rol = "investigador"

        usuario = Usuario(
        nombre=nombre,
        correo=correo,
        password=generate_password_hash(password),
        rol=rol)

        db.session.add(usuario)
        db.session.commit()

        flash("Usuario registrado correctamente")

        return redirect(url_for("login"))

    return render_template("register.html")


# =====================================
# LOGIN
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        correo = request.form["correo"]
        password = request.form["password"]

        usuario = Usuario.query.filter_by(
            correo=correo
        ).first()

        if usuario and check_password_hash(
                usuario.password,
                password):

            login_user(usuario)

            return redirect(url_for("dashboard"))

        flash("Credenciales incorrectas")

    return render_template("login.html")


# =====================================
# DASHBOARD
# =====================================

@app.route("/dashboard")
@login_required
def dashboard():

    total_usuarios = Usuario.query.count()
    total_eventos = Evento.query.count()

    return render_template(
        "dashboard.html",
        total_usuarios=total_usuarios,
        total_eventos=total_eventos
    )


# =====================================
# EVENTOS
# =====================================

@app.route("/eventos")
@login_required
def eventos():

    lista_eventos = Evento.query.all()

    return render_template(
        "eventos.html",
        eventos=lista_eventos
    )


# =====================================
# NUEVO EVENTO
# =====================================

@app.route("/evento/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_evento():

    if current_user.rol != "administrador":
        abort(403)

    if request.method == "POST":

        evento = Evento(
            nombre_evento=request.form["nombre_evento"],
            tipo_evento=request.form["tipo_evento"],
            fecha=request.form["fecha"],
            ubicacion=request.form["ubicacion"],
            descripcion=request.form["descripcion"],
            nivel_riesgo=request.form["nivel_riesgo"]
        )

        db.session.add(evento)
        db.session.commit()

        flash("Evento registrado correctamente")

        return redirect(url_for("eventos"))

    return render_template(
        "form_evento.html",
        titulo="Nuevo Evento",
        evento=None
    )


# =====================================
# EDITAR EVENTO
# =====================================

@app.route("/evento/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_evento(id):

    if current_user.rol != "administrador":
        abort(403)

    evento = Evento.query.get_or_404(id)

    if request.method == "POST":

        evento.nombre_evento = request.form["nombre_evento"]
        evento.tipo_evento = request.form["tipo_evento"]
        evento.fecha = request.form["fecha"]
        evento.ubicacion = request.form["ubicacion"]
        evento.descripcion = request.form["descripcion"]
        evento.nivel_riesgo = request.form["nivel_riesgo"]

        db.session.commit()

        flash("Evento actualizado correctamente")

        return redirect(url_for("eventos"))

    return render_template(
        "form_evento.html",
        titulo="Editar Evento",
        evento=evento
    )


# =====================================
# ELIMINAR EVENTO
# =====================================

@app.route("/evento/eliminar/<int:id>")
@login_required
def eliminar_evento(id):

    if current_user.rol != "administrador":
        abort(403)

    evento = Evento.query.get_or_404(id)

    db.session.delete(evento)
    db.session.commit()

    flash("Evento eliminado correctamente")

    return redirect(url_for("eventos"))


# =====================================
# GESTIÓN DE USUARIOS
# =====================================

@app.route("/usuarios")
@login_required
def usuarios():

    if current_user.rol != "administrador":
        abort(403)

    lista_usuarios = Usuario.query.all()

    return render_template(
        "usuarios.html",
        usuarios=lista_usuarios
    )


# =====================================
# CAMBIAR ROL
# =====================================

@app.route("/usuario/rol/<int:id>")
@login_required
def cambiar_rol(id):

    if current_user.rol != "administrador":
        abort(403)

    usuario = Usuario.query.get_or_404(id)

    if usuario.id == current_user.id:
        flash("No puedes cambiar tu propio rol")
        return redirect(url_for("usuarios"))

    if usuario.rol == "administrador":
        usuario.rol = "investigador"
    else:
        usuario.rol = "administrador"

    db.session.commit()

    flash("Rol actualizado correctamente")

    return redirect(url_for("usuarios"))


# =====================================
# LOGOUT
# =====================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Sesión cerrada correctamente")

    return redirect(url_for("login"))


# =====================================
# ERROR 403
# =====================================

@app.errorhandler(403)
def acceso_denegado(error):

    return render_template(
        "403.html"
    ), 403


# =====================================
# MAIN
# =====================================

if __name__ == "__main__":
    app.run()
