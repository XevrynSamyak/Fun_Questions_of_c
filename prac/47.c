#include <stdio.h>
#define max_size 10
int main(){
    int i,j,a,b,smallest;
    int matrix[max_size][max_size];
    printf("enter the number of the row: ");
    scanf("%d",&a);
    printf("enter the number of the col: ");
    scanf("%d",&b);
    for(i=0;i<a;i++){
        for(j=0;j<b;j++){
            printf("enter the number: ");
            scanf("%d",&matrix[i][j]);
        }
    }
    for (j = 0; j < b; j++){
        int smallest = matrix[0][j];
        for (i = 1; i < a; i++){
            if (matrix[i][j] < smallest){ 
                smallest = matrix[i][j];
            }
            else{
                printf("Smallest element in column %d = %d\n",j + 1, smallest);
            }    
        }
    }
    return 0;
}