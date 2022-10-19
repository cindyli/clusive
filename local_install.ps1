# Run from the root 'clusive' directory after setting up your virtual environment

./env/Scripts/activate
npm install
pip install -r requirements.txt
python -m nltk.downloader wordnet
python -m nltk.downloader omw-1.4
python -m nltk.downloader averaged_perceptron_tagger
grunt build
cd target
python manage.py migrate
python manage.py loaddata preferencesets tiptypes callstoaction subjects
python manage.py importdir ../content
python manage.py import_resources ../resources/resources.json
echo "Setup complete! Run python manage.py createsuperuser to create the super user and you're all done"
cd ..
