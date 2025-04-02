from flask import Blueprint
from Web import csrf
csrf = csrf
front = Blueprint("front", __name__)
from . import index,result,webSearch,snapshot,suggest