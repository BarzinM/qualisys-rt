#include </home/naslab/Barzin/qualisys-rt/Qualisys.h>

int main()
{
    PositionReciever qp;
    Body some_object;
    qp.connect_to_server();

while(1){
    some_object = qp.getStatus();
    // some_object.print();
    printf("%f\n",some_object.position_x);
}

}