from modules.weight_sensor import 

'''


1. 무게를젠다(100ms)
	1-1 전에 무게와 5g이상 차이가 있으면 전에 시점을 그로벌 변수처럼 기록하고 있는다. Start Point
	1-2 한번 3초이상 변화가 없으면 종료시점이라고 판단하여 End Point
	1-3 변화량과 함께 Json 형식으로 아래와 같은 형식으로 data/intake폴더에 저장한다
{
  "serial_number": "SN1234",
  "datetime": "2023-12-25T19:00:15",  # datetime
  "type": "intake",
  "data": {
    "duration": 2,  # integer(분)
    "amount": 20  # integer(그램)
  }
}



2. 초음파센서로 거리를젠다(100ms)
	2-1 거리가 50cm 안쪽으로 들어온다
		2-1-1 카메라를 켠다
		2-1-2 카메라를 3분간 촬영하고 1초 한장씩 180장을 촬영한다 
		2-1-3 카메라 촬영한 사진 data/images에 저장한다


3. . data안에 있는 폴더들을 전부 탐색한다
	3-1 images
		3-1-1 이미지가 있다면 
			3-1-1-1 yolo api를 사용하여 이미지들을 다 yolo를 돌려고보고 눈을 확인한다 
{
  "inference_id": "",
  "time": 0.04207504400073958,
  "image": {
    "width": 500,
    "height": 375
  },
  "predictions": [
    {
      "x": 333.0,
      "y": 141.0,
      "width": 76.0,
      "height": 64.0,
      "confidence": 0.8846404552459717,
      "class": "eye",
      "class_id": 0,
      "detection_id": ""
    },
    {
      "x": 227.0,
      "y": 125.5,
      "width": 64.0,
      "height": 55.0,
      "confidence": 0.8145283460617065,
      "class": "eye",
      "class_id": 0,
      "detection_id": ""
    }
  ]
}

여기서 Confidence가 70이하는 비교도 하지 않고 삭제한다
보내면서 그리디 알고리즘으로 최대값인 것만 보존한다

		3-1-2 답변중 눈을 인식되는 것 외에는 전부삭제한다.
			3-1-2-1 삭제하고 남은 1장을 가지고 오른쪽눈 왼쪽눈을 x y좌표기준으로 하여 자르고 이미지를 저장한다
			3-1-2-2 MovileNetV2 양자화 버전을 5개를 각각 for문으로 돌리고 결과를 
data/eyes에
안구질환 정보 (eye)
{
  "serial_number": "SN1",
  "datetime": "2023-12-25T19:00:15",  # datetime
  "type": "eye",
  "data": {
    "eyes": [
      {
        "eye_side": "right",  // 오른쪽 눈
        "blepharitis_prob": 0.1,  # decimal(3,2)
        "conjunctivitis_prob": 0.2,
        "corneal_sequestrum_prob": 0.3,
        "non_ulcerative_keratitis_prob": 0.4,
        "corneal_ulcer_prob": 0.5, 
        "image_url":"firebase_image_url" or null
      },
      {
        "eye_side": "left",  // 왼쪽 눈
        "blepharitis_prob": 0.1,
        "conjunctivitis_prob": 0.2,
        "corneal_sequestrum_prob": 0.3,
        "non_ulcerative_keratitis_prob": 0.4,
        "corneal_ulcer_prob": 0.5, 
        "image_url":"firebase_image_url" or null
      }
    ]
  }
}
위와 같은 형식으로 저장한다
이미지는 적당한 사이즈로 리사이징하고 firebase로 저장한다

	schedule
	feeding history
	
'''