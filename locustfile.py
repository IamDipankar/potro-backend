# locustfile.py
from locust import FastHttpUser, task, constant

class MyUser(FastHttpUser):
    wait_time = constant(0)  # no think time, push max load
    host = "https://potro-messaging.onrender.com"  # set here so UI host is optional

    # @task
    # def health(self):
    #     # Use a RELATIVE path when host is set
    #     self.client.get("/health", name="/health")

    @task
    def send_message(self):
        self.client.post(
            "/sending/dipankar01",
            params={
                "message": "The name of our country is Bangladesh. it is an independent country"
            },
            name="/sending/dipankar01"
        )

