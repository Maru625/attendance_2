"""
dummy_QR_Camera.py
- 카메라를 열어 QR 인식존(세로 50% 크기의 정사각형)을 중앙에 표시하는 독립 프로그램
- 메인 출석 시스템과 별도로 동작
- 사용법: python dummy_QR_Camera.py [카메라_인덱스]
  - 기본값: 0 (물리 카메라)
  - OBS Virtual Camera 테스트 시 해당 인덱스 사용
- 'q' 키를 누르면 종료
"""

import sys
import cv2
import numpy as np


def main():
    # 카메라 인덱스 (인자로 받거나 기본 0)
    cam_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print(f"카메라 인덱스 {cam_index}을(를) 열 수 없습니다.")
        print("사용 가능한 카메라를 찾는 중...")
        for i in range(5):
            test = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if test.isOpened():
                print(f"  카메라 {i}: 사용 가능")
                test.release()
            else:
                print(f"  카메라 {i}: 없음")
        return

    print(f"=== Dummy QR Camera (카메라 인덱스: {cam_index}) ===")
    print("'q' 키를 누르면 종료합니다.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임을 읽을 수 없습니다.")
            break

        h, w, _ = frame.shape

        # QR 인식존: 세로의 50% 길이를 한 변으로 하는 정사각형, 중앙 배치
        box_size = int(h * 0.5)
        cx, cy = w // 2, h // 2
        x1 = cx - box_size // 2
        y1 = cy - box_size // 2
        x2 = cx + box_size // 2
        y2 = cy + box_size // 2

        # 반투명 오버레이 (인식존 바깥을 어둡게)
        overlay = frame.copy()
        dark = np.zeros_like(frame, dtype=np.uint8)
        overlay = cv2.addWeighted(frame, 0.4, dark, 0.6, 0)
        overlay[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

        # 인식존 테두리 (초록색)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 3)

        # 코너 강조
        corner_len = box_size // 6
        color = (0, 255, 0)
        thickness = 5
        cv2.line(overlay, (x1, y1), (x1 + corner_len, y1), color, thickness)
        cv2.line(overlay, (x1, y1), (x1, y1 + corner_len), color, thickness)
        cv2.line(overlay, (x2, y1), (x2 - corner_len, y1), color, thickness)
        cv2.line(overlay, (x2, y1), (x2, y1 + corner_len), color, thickness)
        cv2.line(overlay, (x1, y2), (x1 + corner_len, y2), color, thickness)
        cv2.line(overlay, (x1, y2), (x1, y2 - corner_len), color, thickness)
        cv2.line(overlay, (x2, y2), (x2 - corner_len, y2), color, thickness)
        cv2.line(overlay, (x2, y2), (x2, y2 - corner_len), color, thickness)

        # 안내 텍스트
        text = "QR Code Zone"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        text_size = cv2.getTextSize(text, font, font_scale, 2)[0]
        text_x = cx - text_size[0] // 2
        text_y = y1 - 15
        cv2.rectangle(overlay, (text_x - 5, text_y - text_size[1] - 5),
                       (text_x + text_size[0] + 5, text_y + 5), (0, 0, 0), -1)
        cv2.putText(overlay, text, (text_x, text_y), font, font_scale, (0, 255, 0), 2)

        # 하단 안내
        cam_label = f"Camera: {cam_index} | Press 'q' to quit"
        cv2.putText(overlay, cam_label, (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Dummy QR Camera", overlay)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("카메라가 종료되었습니다.")


if __name__ == "__main__":
    main()
