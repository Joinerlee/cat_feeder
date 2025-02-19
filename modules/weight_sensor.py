from gpiozero import DigitalInputDevice, DigitalOutputDevice
from time import sleep

class LoadCell:
    """HX711 로드셀 제어를 위한 클래스"""
    
    def __init__(self, dout_pin=15, sck_pin=14):
        """
        로드셀 초기화
        Args:
            dout_pin (int): DOUT 핀 번호 (기본값: 15)
            sck_pin (int): SCK 핀 번호 (기본값: 14)
        """
        self.dout = DigitalInputDevice(dout_pin)
        self.sck = DigitalOutputDevice(sck_pin)
        self.OFFSET = 0
        self.SCALE = 1
        self.is_calibrated = False

    def read_raw_data(self):
        """원시 데이터 읽기"""
        self.sck.off()
        while self.dout.value:
            sleep(0.001)

        data = 0
        for _ in range(24):
            self.sck.on()
            data = data << 1 | self.dout.value
            self.sck.off()

        self.sck.on()
        self.sck.off()
        return data

    def tare(self, times=15):
        """
        영점 조정
        Args:
            times (int): 평균 측정 횟수 (기본값: 15)
        Returns:
            bool: 영점 조정 성공 여부
        """
        try:
            합계 = 0
            for _ in range(times):
                합계 += self.read_raw_data()
            self.OFFSET = 합계 / times
            return True
        except Exception as e:
            print(f"영점 조정 중 오류 발생: {e}")
            return False

    def get_value(self, times=3):
        """
        보정된 값 읽기
        Args:
            times (int): 평균 측정 횟수 (기본값: 3)
        Returns:
            float: 보정된 측정값
        """
        합계 = 0
        for _ in range(times):
            합계 += self.read_raw_data() - self.OFFSET
        return float(합계 / times)

    def get_weight(self, times=3, unit='g'):
        """
        무게 측정
        Args:
            times (int): 평균 측정 횟수 (기본값: 3)
            unit (str): 무게 단위 ('g' 또는 'kg') (기본값: 'g')
        Returns:
            float: 측정된 무게
        """
        if not self.is_calibrated:
            print("경고: 보정이 되지 않은 상태입니다. calibrate()를 먼저 실행하세요.")
        
        값 = self.get_value(times)
        무게 = 값 / self.SCALE
        
        if unit == 'kg':
            무게 = 무게 / 1000
            
        return round(무게, 3)

    def calibrate(self, known_weight_g):
        """
        저울 보정
        Args:
            known_weight_g (float): 기준 무게(g)
        Returns:
            bool: 보정 성공 여부
        """
        try:
            print("보정을 시작합니다...")
            print("1. 저울에서 모든 물체를 제거하세요")
            input("준비되면 Enter를 누르세요...")
            
            self.tare()
            print("영점 조정 완료")
            
            print(f"\n2. {known_weight_g}g 기준 무게를 올려주세요")
            input("준비되면 Enter를 누르세요...")
            
            측정값 = self.get_value()
            self.SCALE = 측정값 / known_weight_g
            self.is_calibrated = True
            
            print("보정이 완료되었습니다!")
            return True
            
        except Exception as e:
            print(f"보정 중 오류 발생: {e}")
            return False

    def start_measurement(self, interval=0.5):
        """
        연속 측정 시작
        Args:
            interval (float): 측정 간격(초) (기본값: 0.5)
        """
        try:
            print("측정을 시작합니다. (종료: Ctrl+C)")
            while True:
                무게 = self.get_weight()
                print(f"현재 무게: {무게}g")
                sleep(interval)
        except KeyboardInterrupt:
            print("\n측정을 종료합니다.")

# 사용 예시
if __name__ == "__main__":
    # 로드셀 객체 생성
    loadcell = LoadCell(dout_pin=5, sck_pin=6)
    
    # 보정 수행 (100g 분동 사용 예시)
    loadcell.calibrate(known_weight_g=100)
    
    # 연속 측정 시작
    loadcell.start_measurement()
