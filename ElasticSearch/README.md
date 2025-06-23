# 📊 Elasticsearch Monitoring Stack (ELK + Beats)

This repository provides a production-ready Docker Compose setup for deploying:

- **Elasticsearch** with SSL and authentication
- **Kibana** for visualization
- **Metricbeat** and **Filebeat** for monitoring and log collection
- **Logstash** for ingest pipelines

Includes secure certificates generation and service health checks.

---

## 🧱 Folder Structure

```
.
├── docker-compose.yml # Full ELK + Beats deployment with TLS
├── .env # Environment variables (not included here)
├── metricbeat.yml # Metricbeat configuration
├── filebeat.yml # Filebeat configuration
├── filebeat_ingest_data/ # Optional Filebeat input data
├── logstash_ingest_data/ # Optional Logstash input data
├── logstash.conf # Logstash pipeline configuration
├── logstash.conf # Logstash pipeline configuration
├── config.py # configuration for elastic server connection
├── createEBESIndex # create index for EB collection
......
```

---

## ⚙️ Requirements

- Docker
- Docker Compose
- Download ingest data from [this link](https://uoe-my.sharepoint.com/:f:/g/personal/s2047051_ed_ac_uk/ErJKtYx_JRhGsgeNFtvC9v0BH361-oZDtsWZxr7sPd_Srw?email=a.krause%40epcc.ed.ac.uk&e=7Mf4gO) and put it in `ingest_data` folder.

---

## 🔐 Setup

1. **Modify `.env` file**: change the hostname, ports, passwords.
2. **Start the server**

    ```shell
    docker-compose up -d
    ```
    This will:
   * Generate TLS certificates
   * Set Kibana system password
   * Start all services (Elasticsearch, Kibana, Beats, Logstash)

3. **Access Kibana**
 
    * Visit: http://localhost:5601
    * Login as elastic using the password from your .env

4. **Copy TLS certificate in current folder**

   ```shell
   # go to es container
   sudo docker exec -it frances-elastic-es01-1 sh
   # in the container, run
   more /usr/share/elasticsearch/config/certs/ca/ca.crt
   ```
   You will see the certificate, create `ca.crt` with the certificate information in current folder, and modify the `config.py` accordingly.

5. **Create index for EB collection**

   1. Create API key from kibana http://localhost:5601
   2. Modify `config.py` accordingly
   3. run the following command: 
    ```shell
   python createEBESIndex.py
   ```