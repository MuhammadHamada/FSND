#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='venue', lazy=True, cascade="all, delete")

    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='artist', lazy=True, cascade="all, delete")

    def __repr__(self):
        return f'<Artist {self.id} {self.name} >'

class Show(db.Model):

    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show {self.id} {self.artist_id} {self.venue_id} {self.start_time}>'


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.order_by('city','state','id').all()
  data = []
  preCity = ""
  preState = ""
  indx = -1
  for venue in venues:
    curCity = venue.city
    curState = venue.state
    if (curCity != preCity or curState != preState):
      data.append({"city": curCity, "state": curState, "venues":[]})
      indx += 1
    num_upcoming_shows = db.session.query(Show).filter(Show.venue_id == venue.id, str(Show.start_time) > str(datetime.now())).count()
    data[indx]["venues"].append({"id": venue.id, "name": venue.name, "num_upcoming_shows": num_upcoming_shows})
    preCity = curCity
    preState = curState

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  search = "%{}%".format(search_term)
  venues = Venue.query.filter(Venue.name.like(search)).all()
  numOfResults = len(venues)
  response={
    "count": numOfResults,
    "data": []
  }
  for i in range(numOfResults):
    x = {}
    x["id"] = venues[i].id
    x["name"] = venues[i].name
    x["num_upcoming_shows"] = 0
    response["data"].append(x)

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = Venue.query.get(venue_id)

  list_shows = db.session.query(Show).filter(Show.venue_id == venue_id)
  past_shows = []
  upcoming_shows = []
  for show in list_shows:
    artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id == show.artist_id).one()
    
    show_add = {
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": str(show.start_time)
    }

    if (str(show.start_time) < str(datetime.now())):
        past_shows.append(show_add)
    else:
        upcoming_shows.append(show_add)
  
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": [venue.genres],
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # insert form data as a new Venue record in the db, instead
  form = VenueForm(request.form, meta={'csrf': False})
  try:
      venue = Venue(
          name=form.name.data,
          city=form.city.data,
          state=form.state.data,
          address=form.address.data,
          phone=form.phone.data,
          genres=form.genres.data,
          facebook_link=form.facebook_link.data,
          image_link=form.image_link.data,
          website_link=form.website_link.data,
          seeking_talent=form.seeking_talent.data,
          seeking_description=form.seeking_description.data
      )
      # modify data to be the data object returned from db insertion
      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + form.name.data + ' was successfully listed!')
  except ValueError as e:
      # on unsuccessful db insert, flash an error instead.
      print(e)
      db.session.rollback()
      flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
  finally:
      db.session.close()
  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  body = {}
  name = ""
  try:
    venue = Venue.query.get(venue_id)
    name = venue.name
    db.session.delete(venue)
    db.session.commit()
    body['name']= venue.name
    body['id'] = venue.id
    flash('Venue ' + name + ' was successfully deleted!')
  except ValueError as e:
    print(e)
    db.session.rollback()
    flash('Error : Venue ' + name + ' could not be deleted!')
  finally:
    db.session.close()
  if error:
    abort (400)
  else:
    return jsonify(body)

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.order_by('id').all()
  data = []
  for artist in artists:
    x = {}
    x["id"] = artist.id
    x["name"] = artist.name
    data.append(x)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  error = False
  body = {}
  name = ""
  try:
    artist = Artist.query.get(artist_id)
    name = artist.name
    db.session.delete(artist)
    db.session.commit()
    body['name']= artist.name
    body['id'] = artist.id
    flash('Artist ' + name + ' was successfully deleted!')
  except ValueError as e:
    print(e)
    db.session.rollback()
    flash('Error : Artist ' + name + ' could not be deleted!')
  finally:
    db.session.close()
  if error:
    abort (400)
  else:
    return jsonify(body)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  search = "%{}%".format(search_term)
  artists = Artist.query.filter(Artist.name.like(search)).all()
  numOfResults = len(artists)
  response={
    "count": numOfResults,
    "data": []
  }
  for i in range(numOfResults):
    x = {}
    x["id"] = artists[i].id
    x["name"] = artists[i].name
    x["num_upcoming_shows"] = 0
    response["data"].append(x)

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist = Artist.query.get(artist_id)

  list_shows = db.session.query(Show).filter(Show.artist_id == artist_id)
  past_shows = []
  upcoming_shows = []
  for show in list_shows:
    venue = db.session.query(Venue.name, Venue.image_link).filter(Venue.id == show.venue_id).one()
    
    show_add = {
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link,
        "start_time": str(show.start_time)
    }

    if (str(show.start_time) < str(datetime.now())):
        past_shows.append(show_add)
    else:
        upcoming_shows.append(show_add)

  data={
    "id": artist.id,
    "name": artist.name,
    "genres": [artist.genres],
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": [artist.genres],
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link  
    }
  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  print(artist)
  form = ArtistForm(request.form)
  try:
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = form.genres.data
      artist.facebook_link = form.facebook_link.data
      artist.image_link = form.image_link.data
      artist.website_link = form.website_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data
      db.session.commit()
      flash('Artist ' + artist.name + ' was successfully edited!')
  except ValueError:
      db.session.rollback()
      flash('Error! Artist ' + artist.name + ' could not be listed.')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": [venue.genres],
    "city": venue.city,
    "state": venue.state,
    "address": venue.address,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link  
    }
  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  form = VenueForm(request.form)
  try:
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.genres = form.genres.data
      venue.facebook_link = form.facebook_link.data
      venue.image_link = form.image_link.data
      venue.website_link = form.website_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data
      db.session.commit()
      flash('Venue ' + venue.name + ' was successfully edited!')
  except ValueError:
      db.session.rollback()
      flash('Error! Venue ' + venue.name + ' could not be listed.')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # insert form data as a new Artist record in the db, instead
  form = ArtistForm(request.form, meta={'csrf': False})
  try:
      artist = Artist(
          name=form.name.data,
          city=form.city.data,
          state=form.state.data,
          phone=form.phone.data,
          genres=form.genres.data,
          facebook_link=form.facebook_link.data,
          image_link=form.image_link.data,
          website_link=form.website_link.data,
          seeking_venue=form.seeking_venue.data,
          seeking_description=form.seeking_description.data
      )
      # modify data to be the data object returned from db insertion
      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + form.name.data + ' was successfully listed!')
  except ValueError as e:
      # on unsuccessful db insert, flash an error instead.
      print(e)
      db.session.rollback()
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
  finally:
      db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.order_by('id').all()
  data = []
  for show in shows:
    x = {}
    artist = Artist.query.get(show.artist_id)
    x["venue_id"] = show.venue_id
    x["venue_name"] = Venue.query.get(show.venue_id).name
    x["artist_id"] = show.artist_id
    x["artist_name"] = artist.name
    x["artist_image_link"] = artist.image_link
    x["start_time"] = show.start_time
    data.append(x)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # insert form data as a new Show record in the db, instead
  form = ShowForm(request.form, meta={'csrf': False})
  try:
      show = Show(
          artist_id=form.artist_id.data,
          venue_id=form.venue_id.data,
          start_time=form.start_time.data
      )
      # modify data to be the data object returned from db insertion
      db.session.add(show)
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')
  except ValueError as e:
      # on unsuccessful db insert, flash an error instead.
      print(e)
      db.session.rollback()
      flash('An error occurred. Show could not be listed.')
  finally:
      db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
