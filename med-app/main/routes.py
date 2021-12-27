import joblib
import numpy as np
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required, login_user
from flask_security import logout_user
from werkzeug.security import check_password_hash
from models.user import User
from extensions import db, login_manager, bcrypt
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import warnings

# warnings.filterwarnings("ignore")

filename = 'diabetes-prediction-rfc-model.pkl'
classifier = pickle.load(open(filename, 'rb'))
model = pickle.load(open('model.pkl', 'rb'))
model1 = pickle.load(open('model1.pkl', 'rb'))
main = Blueprint('main', __name__, static_folder='../static', template_folder='../templates')


def get_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    return user


@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)


@main.route('/login')
def login():
    return render_template('security/login_user.html')


@main.route('/sign-in', methods=['POST', 'GET'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    # remember_me = True if request.form.get('remember') else False
    user = User.query.filter_by(email=email).first()
    if user and user.verify_password(password) and user.active==1:
        login_user(user)
        flash(f"Hi {user.username}!", "success")
        if user.roles[0].name.__eq__("patient"):
            return redirect(url_for('patient.pat_dash'))
        if user.roles[0].name.__eq__("admin"):
            return redirect(url_for('admin.admin_dash'))
        if user.roles[0].name.__eq__("doctor"):
            return redirect(url_for('doctor.doc_dash'))
        else:
            flash("Error! Recreate your account, please")
            return "NO DEFINED ROLE"

    flash("Invalid Password/ Email. Please Try Again!")
    return render_template("security/login_user.html")


@main.route("/")
def index():
    return render_template("index.html")


@main.route('/about')
def about():
    return render_template("about.html")


@main.route('/help')
def help():
    return render_template("help.html")


@main.route('/terms')
def terms():
    return render_template("tc.html")


@main.route("/home")
@login_required
def home():
    return f"{current_user.username}. Your email is {current_user.email}"


@main.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


@main.errorhandler(500)
def internal_server_error(e):
    # note that we set the 500 status explicitly
    return render_template('500.html'), 500


@main.route("/add_phone_number")
@login_required
def add_phone():
    return render_template("/security/add_phone.html")


@main.route("/update_phone", methods=["GET", "POST"])
@login_required
def update_phone():
    if request.method == "POST":
        phone_number = request.form["phone_number"]
        # user = User.query.filter_by(email=current_user.email).first()
        user_updated = User.query.filter_by(id=current_user.id).update(dict(phone=phone_number))
        db.session.commit()
    return redirect("/home")


@main.route("/dashboard")
@login_required
def dashboard():
    return render_template("diseases/dashboard.html")


@main.route("/disindex")
def disindex():
    return render_template("diseases/disindex.html")


@main.route("/cancer")
@login_required
def cancer():
    return render_template("diseases/cancer.html")


@main.route("/diabetes")
@login_required
def diabetes():
    return render_template("diseases/diabetes.html")


@main.route("/heart")
@login_required
def heart():
    return render_template("diseases/heart.html")


@main.route("/kidney")
@login_required
def kidney():
    return render_template("diseases/kidney.html")


def ValuePredictor(to_predict_list, size):
    to_predict = np.array(to_predict_list).reshape(1, size)
    if size == 7:
        loaded_model = joblib.load('kidney_model.pkl')
        result = loaded_model.predict(to_predict)
    return result[0]


@main.route("/predictkidney", methods=['GET', 'POST'])
def predictkidney():
    if request.method == "POST":
        to_predict_list = request.form.to_dict()
        to_predict_list = list(to_predict_list.values())
        to_predict_list = list(map(float, to_predict_list))
        if len(to_predict_list) == 7:
            result = ValuePredictor(to_predict_list, 7)
    if (int(result) == 1):
        prediction = "Patient has a high risk of Kidney Disease, please consult your doctor immediately"
    else:
        prediction = "Patient has a low risk of Kidney Disease"
    return render_template("diseases/kidney_result.html", prediction_text=prediction)


@main.route("/liver")
@login_required
def liver():
    return render_template("diseases/liver.html")


def ValuePred(to_predict_list, size):
    to_predict = np.array(to_predict_list).reshape(1, size)
    if (size == 7):
        loaded_model = joblib.load('liver_model.pkl')
        result = loaded_model.predict(to_predict)
    return result[0]


@main.route('/predictliver', methods=["POST"])
def predictliver():
    if request.method == "POST":
        to_predict_list = request.form.to_dict()
        to_predict_list = list(to_predict_list.values())
        to_predict_list = list(map(float, to_predict_list))
        if len(to_predict_list) == 7:
            result = ValuePred(to_predict_list, 7)

    if int(result) == 1:
        prediction = "Patient has a high risk of Liver Disease, please consult your doctor immediately"
    else:
        prediction = "Patient has a low risk of Kidney Disease"
    return render_template("diseases/liver_result.html", prediction_text=prediction)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for(''))


@main.route('/predict', methods=['POST'])
def predict():
    input_features = [int(x) for x in request.form.values()]
    features_value = [np.array(input_features)]
    features_name = ['clump_thickness', 'uniform_cell_size', 'uniform_cell_shape', 'marginal_adhesion',
                     'single_epithelial_size', 'bare_nuclei', 'bland_chromatin', 'normal_nucleoli', 'mitoses']
    df = pd.DataFrame(features_value, columns=features_name)
    output = model.predict(df)
    if output == 4:
        res_val = "a high risk of Breast Cancer"
    else:
        res_val = "a low risk of Breast Cancer"

    return render_template('diseases/cancer_result.html', prediction_text=f'Patient has {res_val}')


##################################################################################

df1 = pd.read_csv('diabetes.csv')

# Renaming DiabetesPedigreeFunction as DPF
df1 = df1.rename(columns={'DiabetesPedigreeFunction': 'DPF'})

# Replacing the 0 values from ['Glucose','BloodPressure','SkinThickness','Insulin','BMI'] by NaN
df_copy = df1.copy(deep=True)
df_copy[['Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI']] = df_copy[['Glucose', 'BloodPressure',
                                                                                    'SkinThickness', 'Insulin',
                                                                                    'BMI']].replace(0, np.NaN)

# Replacing NaN value by mean, median depending upon distribution
df_copy['Glucose'].fillna(df_copy['Glucose'].mean(), inplace=True)
df_copy['BloodPressure'].fillna(df_copy['BloodPressure'].mean(), inplace=True)
df_copy['SkinThickness'].fillna(df_copy['SkinThickness'].median(), inplace=True)
df_copy['Insulin'].fillna(df_copy['Insulin'].median(), inplace=True)
df_copy['BMI'].fillna(df_copy['BMI'].median(), inplace=True)

# Model Building

X = df1.drop(columns='Outcome')
y = df1['Outcome']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=0)

# Creating Random Forest Model

classifier = RandomForestClassifier(n_estimators=20)
classifier.fit(X_train, y_train)

# Creating a pickle file for the classifier
filename = 'diabetes-prediction-rfc-model.pkl'
pickle.dump(classifier, open(filename, 'wb'))


#####################################################################


@main.route('/predictt', methods=['POST'])
def predictt():
    if request.method == 'POST':
        preg = request.form['pregnancies']
        glucose = request.form['glucose']
        bp = request.form['bloodpressure']
        st = request.form['skinthickness']
        insulin = request.form['insulin']
        bmi = request.form['bmi']
        dpf = request.form['dpf']
        age = request.form['age']

        data = np.array([[preg, glucose, bp, st, insulin, bmi, dpf, age]])
        my_prediction = classifier.predict(data)

        return render_template('diseases/diab_result.html', prediction=my_prediction)


############################################################################################################

@main.route('/predictheart', methods=['POST'])
def predictheart():
    input_features = [float(x) for x in request.form.values()]
    features_value = [np.array(input_features)]

    features_name = ["age", "trestbps", "chol", "thalach", "oldpeak", "sex_0",
                     "  sex_1", "cp_0", "cp_1", "cp_2", "cp_3", "  fbs_0",
                     "restecg_0", "restecg_1", "restecg_2", "exang_0", "exang_1",
                     "slope_0", "slope_1", "slope_2", "ca_0", "ca_1", "ca_2", "thal_1",
                     "thal_2", "thal_3"]

    df = pd.DataFrame(features_value, columns=features_name)
    output = model1.predict(df)

    if output == 1:
        res_val = "a high risk of Heart Disease"
    else:
        res_val = "a low risk of Heart Disease"

    return render_template('diseases/heart_result.html', prediction_text='Patient has {}'.format(res_val))
