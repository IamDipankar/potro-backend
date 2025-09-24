# locustfile.py
from locust import FastHttpUser, task, constant
import random

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
            name="/sending/dipankar02"
        )

    # @task
    # def get_messages(self):
    #     access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImRpcGFua2FyMDIiLCJleHAiOjE3NTg2OTc3MTF9.mBKQkO0BxwuirA3WNK4bMtmEms4ZACq9Hryk5Yxjiks"
    #     msg_id_list = [19400,19399,19398,19397,19396,19395,19394,19393,19392,19391,19390,19389,19388,19387,19386,19385,19384,19383,19382,19381,19380,19379,19378,19377,19376,19375,19374,19373,19372,19371,19370,19369,19368,19367,19366,19365,19364,19363,19362,19361,19360,19359,19358,19357,19356,19355,19354,19353,19352,19351,19350,19349,19348,19347,19346,19345,19344,19343,19342,19341,19340,19339,19338,19337,19336,19335,19334,19333,19332,19331,19330,19329,19328,19327,19326,19325,19324,19323,19322,19321,19320,19319,19318,19317,19316,19315,19314,19313,19312,19311,19310,19309,19308,19307,19306,19305,19304,19303,19302,19301]
    #     msg_id = random.choice(msg_id_list)
    #     self.client.patch(
    #         f'/recieving/mark_read/{msg_id}',
    #         headers={"Authorization": f"Bearer {access_token}"}
    #     )

