"""这个项目额外的url，比如功能的url，这个需要新写"""

from flask import render_template, request, session, make_response, Blueprint, redirect, url_for, jsonify, send_from_directory

from get_app import app

"""
项目通用的url链接,后期需要根据实际情况简单修改
"""
web_bp = Blueprint('speech', import_name=__name__, url_prefix='')
