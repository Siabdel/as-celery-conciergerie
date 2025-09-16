## build docker 
sudo docker-compose -f docker-compose.prod.yml up -d --build
## se connecter au docker 
sudo docker-compose -f docker-compose.prod.yml exec web  bash
sudo docker-compose -f docker-compose.prod.yml exec db   bash
## executer une commande
docker exec -i conciergerie_db ls -l  -U postgres 
