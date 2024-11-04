FROM postgres:14.0-alpine

# CMD set -xea;

WORKDIR /src
#
#Removing intermediate container 
RUN set -eux
#
RUN apk update && apk  upgrade 
RUN apk add bash vim 
#RUN pip install --upgrade pip

# copy dump files 
COPY . .
###
# run entrypoint.sh
# ENTRYPOINT [“executable”, “param1”, “param2”, ..]
#ENTRYPOINT ["/src/entrypoint.sh" ]
#CMD  "/src/entrypoint.sh" 
#ENTRYPOINT ["/src/entrypoint.sh" ]