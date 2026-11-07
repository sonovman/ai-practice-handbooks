/* 핸드북 21 시범용 — 내가 직접 작성한 프로그램입니다(자작 바이너리 역공학 실습 대상).
   화면 x좌표(0~639)를 좌우 스피커 팬 값(-1.0 ~ +1.0)으로 바꾸는 작은 함수. */
#include <stdio.h>

double compute_pan(int x) {
    double center = 320.0;   /* 화면 가로 중앙 */
    double scale  = 0.003125; /* 1/320 : 가장자리에서 ±1.0 */
    double pan = ((double)x - center) * scale;
    if (pan < -1.0) pan = -1.0;
    if (pan >  1.0) pan =  1.0;
    return pan;
}

int main(void) {
    int xs[] = {0, 160, 320, 480, 639};
    for (int i = 0; i < 5; i++)
        printf("x=%3d -> pan=%+.4f\n", xs[i], compute_pan(xs[i]));
    return 0;
}
