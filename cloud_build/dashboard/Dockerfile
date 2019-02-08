FROM python:3.6

RUN mkdir /compatibility_dashboard
RUN mkdir /compatibility_dashboard/dashboard
RUN mkdir /static
ADD static/ /static/
ADD main-template.html /compatibility_dashboard/dashboard/
ADD grid-template.html /compatibility_dashboard/dashboard/
ADD dashboard_builder.py /compatibility_dashboard/dashboard/
ADD requirements-test.txt /compatibility_dashboard
ADD python-compatibility-tools.json /compatibility_dashboard
ENV GOOGLE_APPLICATION_CREDENTIALS=/compatibility_dashboard/python-compatibility-tools.json

RUN pip3 install -r /compatibility_dashboard/requirements-test.txt

RUN cd /compatibility_dashboard && python dashboard/dashboard_builder.py && cp dashboard/index.html /static/ && cp dashboard/grid.html /static/
