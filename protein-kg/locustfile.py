from locust import HttpUser, task, between

class ProteinSearchUser(HttpUser):
    wait_time = between(0.1, 0.5)  # 模拟用户思考间隔

    @task(3)
    def search_sequence(self):
        seq = "MEEPQSDPSVEPPLSQETFSDLWKLL"
        self.client.post("/search", json={"sequence": seq, "top_k": 5})

    @task(1)
    def search_function(self):
        self.client.get("/search/function?q=kinase&top_k=5")