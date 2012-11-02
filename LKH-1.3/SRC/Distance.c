#include "LK.h"

/* 
   Functions for computing distances (see TSPLIB).

   The appropriate function is referenced by the function pointer Distance.
*/

long Distance_1(Node * Na, Node * Nb)
{
    return 1;
}

long Distance_ATSP(Node * Na, Node * Nb)
{
    long n = Dimension / 2;
    if ((Na->Id <= n) == (Nb->Id <= n))
        return M;
    if (labs(Na->Id - Nb->Id) == n)
        return 0;
    return Na->Id < Nb->Id ? Na->C[Nb->Id - n] : Nb->C[Na->Id - n];
}

long Distance_ATT(Node * Na, Node * Nb)
{
    double xd = Na->X - Nb->X, yd = Na->Y - Nb->Y;
    return ceil(sqrt((xd * xd + yd * yd) / 10.0));
}

long Distance_CEIL_2D(Node * Na, Node * Nb)
{
    double xd = Na->X - Nb->X, yd = Na->Y - Nb->Y;
    return ceil(sqrt(xd * xd + yd * yd));
}

long Distance_CEIL_3D(Node * Na, Node * Nb)
{
    double xd = Na->X - Nb->X, yd = Na->Y - Nb->Y, zd = Na->Z - Nb->Z;
    return ceil(sqrt(xd * xd + yd * yd + zd * zd));
}

long Distance_EXPLICIT(Node * Na, Node * Nb)
{
    return Na->Id < Nb->Id ? Nb->C[Na->Id] : Na->C[Nb->Id];
}

long Distance_EUC_2D(Node * Na, Node * Nb)
{
    double xd = Na->X - Nb->X, yd = Na->Y - Nb->Y;
    return sqrt(xd * xd + yd * yd) + 0.5;
}

long Distance_EUC_3D(Node * Na, Node * Nb)
{
    double xd = Na->X - Nb->X, yd = Na->Y - Nb->Y, zd = Na->Z - Nb->Z;
    return sqrt(xd * xd + yd * yd + zd * zd) + 0.5;
}

#define PI 3.141592
#define RRR 6378.388

double Acos(double x);
double Acos(double x)
{
    if (strcmp(Name, "ali535") == 0) {
        /* This small hack was made in order to get the correct 
           distances for this problem */
        float v = x;
        return PI / 2.0 - atan(v / sqrt(1.0 - v * v));
    }
    return acos(x);
}

long Distance_GEO(Node * Na, Node * Nb)
{
    long deg;
    double NaLatitude, NaLongitude, NbLatitude, NbLongitude, min, q1, q2,
        q3;
    deg = Na->X;
    min = Na->X - deg;
    NaLatitude = PI * (deg + 5.0 * min / 3.0) / 180.0;
    deg = Na->Y;
    min = Na->Y - deg;
    NaLongitude = PI * (deg + 5.0 * min / 3.0) / 180.0;
    deg = Nb->X;
    min = Nb->X - deg;
    NbLatitude = PI * (deg + 5.0 * min / 3.0) / 180.0;
    deg = Nb->Y;
    min = Nb->Y - deg;
    NbLongitude = PI * (deg + 5.0 * min / 3.0) / 180.0;
    q1 = cos(NaLongitude - NbLongitude);
    q2 = cos(NaLatitude - NbLatitude);
    q3 = cos(NaLatitude + NbLatitude);
    return RRR * Acos(0.5 * ((1.0 + q1) * q2 - (1.0 - q1) * q3)) + 1.0;
}

#undef M_PI
#define M_PI 3.14159265358979323846264

long Distance_GEOM(Node * Na, Node * Nb)
{
    double lati = M_PI * (Na->X / 180.0);
    double latj = M_PI * (Nb->X / 180.0);
    double longi = M_PI * (Na->Y / 180.0);
    double longj = M_PI * (Nb->Y / 180.0);
    double q1 = cos(latj) * sin(longi - longj);
    double q3 = sin((longi - longj) / 2.0);
    double q4 = cos((longi - longj) / 2.0);
    double q2 = sin(lati + latj) * q3 * q3 - sin(lati - latj) * q4 * q4;
    double q5 = cos(lati - latj) * q4 * q4 - cos(lati + latj) * q3 * q3;
    return (long) (6378388.0 * atan2(sqrt(q1 * q1 + q2 * q2), q5) + 1.0);
}

long Distance_MAN_2D(Node * Na, Node * Nb)
{
    return fabs(Na->X - Nb->X) + fabs(Na->Y - Nb->Y) + 0.5;
}

long Distance_MAN_3D(Node * Na, Node * Nb)
{
    return fabs(Na->X - Nb->X) +
        fabs(Na->Y - Nb->Y) + fabs(Na->Z - Nb->Z) + 0.5;
}

long Distance_MAX_2D(Node * Na, Node * Nb)
{
    long dx = fabs(Na->X - Nb->X) + 0.5, dy = fabs(Na->Y - Nb->Y) + 0.5;
    return dx > dy ? dx : dy;
}

long Distance_MAX_3D(Node * Na, Node * Nb)
{
    long dx = fabs(Na->X - Nb->X) + 0.5, dy = fabs(Na->Y - Nb->Y) + 0.5,
        dz = fabs(Na->Z - Nb->Z) + 0.5;
    if (dy > dx)
        dx = dy;
    return dx > dz ? dx : dz;
}
