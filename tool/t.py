from werkzeug.utils import secure_filename
filename = '12.df.dfasd=d=fads.png'
safe_filename = secure_filename(filename)
print(safe_filename)
