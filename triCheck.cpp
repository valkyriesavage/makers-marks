#include <vector>
#include <iostream>
#include <sstream>
#include <fstream>
#include <cmath>
#include <math.h>
#include <map>
#include "Vector.h"
#include <tuple>

using namespace std;

// ***********************************
// Given a centroid (in u,v) and an obj
// file, this program returns the 3D coordinates
// of the centroid.
// Arguments: obj jpg lu lv cu cv ru rv
// ***********************************
bool correct_jpg = false;

class Triangle {
public:
	Vector a;
	Vector b;
	Vector c;
	void Set(Vector pa, Vector pb, Vector pc){a=pa, b=pb, c=pc;}
};

std::ostream& operator<< (std::ostream &out, Triangle &triangle)
{
    out << "Triangle: (" << triangle.a << ", " <<
        triangle.b<< ", " <<
        triangle.c << ")\n";
    return out;
}

//Checks if p1 and p2 are in the same side of a triangle.
bool sameSide(Vector p1, Vector p2, Vector ta, Vector tb) {
	Vector cp1 = (tb - ta).cross(p1 - ta);
	Vector cp2 = (tb - ta).cross(p2 - ta);
	if (cp1.dot(cp2) >= 0)
		return true;
	return false;
}

//Returns T/F if a point is in a triangle.
bool pointInTriangle(Vector point, Triangle tri) {
	Vector a = tri.a;
	Vector b = tri.b;
	Vector c = tri.c;
	//line
	if (a.x == b.x && b.x == c.x && c.x == a.x)
		return false;
	if (a.y == b.y && b.y == c.y && c.y == a.y) {
		return false;			
	}
	if (sameSide(point, a, b, c) && sameSide(point, b, a, c) && sameSide(point, c, a, b))
		return true;
	return false;
}

//Reads the .MTL file for jpg discrimination. 
void read_mtl(istream& stream, map<string, string> * materials) {
	string line;
	getline(stream, line); //reads line by line
	string buf;
    stringstream ss(line);
    vector<string> tokens;
    const char *l = line.c_str();	

    if (strncmp(l, "newmtl", 6) == 0) {
	    while (ss >> buf) {
	      tokens.push_back(buf);
	    }
		string newmtl = tokens[1];
		string line2;
		getline(stream, line2);
		stringstream ss2(line2);
	    while (ss2 >> buf) {
	      tokens.push_back(buf);
	    }
	    string jpg = tokens[3];
		materials->insert(pair<string, string>(newmtl, jpg));
    }
}



//Takes in an obj file, fills the passed in obj vector of triangles in return.
// I'm sorry this takes in so many arguments :(
void read_line(istream& stream, vector<Vector> * vertices, vector<Vector> *three_d_v, vector<Triangle> * triangles, vector<Triangle> * three_d_tri, char * jpg_filename, map<string, string> * materials) {
	string line;
	getline(stream, line); //reads line by line
	const char *l = line.c_str();	
	if (strncmp(l, "v ", 2) == 0) {
	    string buf;
	    stringstream ss(line);
	    vector<string> tokens;
	    while (ss >> buf) {
	      tokens.push_back(buf);
	    }
	    for (int i = 0; i < tokens.size(); i+=4) {
	      //get rid of Vs, load 3 points as a coordinate
	      Vector pts = Vector(stof(tokens[i+1], NULL), stof(tokens[i+2], NULL),stof(tokens[i+3], NULL));
	      three_d_v->push_back(pts);
		}
	}
	if (strncmp(l, "vt ", 3) == 0) {
		string buf;
		stringstream ss(line);
		vector<string> tokens;
		while (ss >> buf) {
			tokens.push_back(buf);
		}
		for (int i = 0; i < tokens.size(); i += 3) {
			//get rid of Vs, load 2 points as a coordinate 
			Vector pts = Vector(stof(tokens[i+1], NULL), stof(tokens[i+2], NULL), 0.0);
			vertices->push_back(pts);
		}
	}
	else if (strncmp(l, "mtllib", 6) == 0) { 
		//open the .mtl file
		string buf;
		stringstream ss(line);
		vector<string> tokens;
		while (ss >> buf) {
			tokens.push_back(buf); //tokens[0] = mtllib, tokens[1] = xxx.mtl
		}
		string path = "obj/" + tokens[1];
		ifstream mtlFile(path);
		int ind = 1;
		if (mtlFile.is_open()) {
			while (mtlFile.good()) {
				read_mtl(mtlFile, materials);
			}
			mtlFile.close();
		}
		else {
			cout << "NOTE: Can not open .mtl file." << endl;
		}
	}
	else if (strncmp(l, "usemtl", 6) == 0) {
		string buf;
		stringstream ss(line);
		vector<string> tokens;
		while (ss >> buf) {
			tokens.push_back(buf);
		}
		map<string, string>::iterator it = (*materials).find(tokens[1]);
		string value = it->second;
		//I can't believe I still need to convert this...
		const char *v = value.c_str();	
		if (strcmp(v, jpg_filename) == 0) {
			correct_jpg = true;
		}
		else {
			correct_jpg = false;
		}
	}
	else if (correct_jpg && strncmp(l, "f ", 2) == 0) {
		string buf;
		stringstream ss(line);
		vector<string> tokens;
		while (ss >> buf) {
			tokens.push_back(buf);
		}
		string slash = "/";
		for (int i = 0; i < tokens.size(); i += 4) {
			//break each token by its slash
			string v1 = tokens[i+1];
			string v2 = tokens[i+2];
			string v3 = tokens[i+3];
			int v1i = stoi(v1.substr(0, v1.find(slash))) - 1; //v1 is f v1, aka the index of the vertex
			int v2i = stoi(v2.substr(0, v2.find(slash))) - 1;
			int v3i = stoi(v3.substr(0, v3.find(slash))) - 1; //-1 bc 1 indexed
			//find vertices, add them to objects
			Triangle tri;
			Triangle three_dt;
			tri.Set((*vertices)[v1i], (*vertices)[v2i], (*vertices)[v3i]);
			three_dt.Set((*three_d_v)[v1i], (*three_d_v)[v2i], (*three_d_v)[v3i]);
			triangles->push_back(tri);
			three_d_tri->push_back(three_dt);
		}
	}
}


//calls everything else if obj file is valid.
void triCheck(char * filename, vector<Vector> * vertices, vector<Vector> * three_d_v, vector<Triangle> * triangles, vector<Triangle> * three_d_tri, char * jpg_filename, map<string, string> * materials){
	string path = "obj/" + string(filename);
	ifstream objFile(path);
	if (objFile.is_open()) {
		while (objFile.good()) {
			read_line(objFile, vertices, three_d_v, triangles, three_d_tri, jpg_filename, materials);
		}
		objFile.close();
	}
	else {
		cout << "NOTE: Can not open .obj file." << endl;
	}
}

//returns centroid, normal vectors of a triangle
tuple<Vector, Vector> centroid(Triangle tri) {
	Vector centroid = (tri.a + tri.b + tri.c) / 3;
	Vector p2_m_p1 = tri.b - tri.a;
	Vector p3_m_p1 = tri.c - tri.a;
	Vector normal = p2_m_p1.cross(p3_m_p1);
	normal = normal.normalize();
	return make_tuple(centroid, normal);
}

//commandline: xxx.obj filename.jpg uLeft vLeft uCenter uCenter uRight lRight
int main(int argc, char *argv[]) {
	if (argc != 9) {
		cerr << "Invalid number of arguments!" << endl;
		return 0;
	}
	if (strtof(argv[3], NULL) > 1 || strtof(argv[4], NULL) > 1 || strtof(argv[5], NULL) > 1 || strtof(argv[6], NULL) > 1 || strtof(argv[7], NULL) > 1 || strtof(argv[8], NULL) > 1) {
		cerr << "u, v must be <= 1" << endl; 
		return 0;
	}
	vector<Vector> vertices;
	vector<Vector> three_d_v;
	vector<Triangle> triangles;
	vector<Triangle> three_d_tri;
	char * jpg_filename = argv[2];
	map<string, string> materials;
	Vector left_point = Vector(strtof(argv[3], NULL), strtof(argv[4], NULL), 0);
	Vector center_point = Vector(strtof(argv[5], NULL), strtof(argv[6], NULL), 0);
	Vector right_point = Vector(strtof(argv[7], NULL), strtof(argv[8], NULL), 0);
	triCheck(argv[1], &vertices, &three_d_v, &triangles, &three_d_tri, jpg_filename, &materials);
	
	Triangle left;
	Triangle left3d;
	Triangle center;
	Triangle center3d;
	Triangle right;
	Triangle right3d;

	//This assumes there is only 1 triangle that works.
	for (int i = 0; i < triangles.size(); i++) {
		if (pointInTriangle(left_point, triangles[i])){
			left = triangles[i];
			left3d = three_d_tri[i];
		}
		else if (pointInTriangle(center_point, triangles[i])){
			center = triangles[i];
			center3d = three_d_tri[i];
		}
		else if (pointInTriangle(right_point, triangles[i])){
			right = triangles[i];
			right3d = three_d_tri[i];
		}
	}
	//Just uses center normal
	/*cout << "Left triangle: " << left << endl;
	cout << "3D triangle: " << left3d << endl;*/
	tuple<Vector, Vector> cn_l = centroid(left3d);
	cout << "Left " << get<0>(cn_l);
	tuple<Vector, Vector> cn_c = centroid(center3d);
	cout << "Center " << get<0>(cn_c);
	tuple<Vector, Vector> cn_r = centroid(right3d);
	cout << "Right " << get<0>(cn_r);
	cout << "Normal " << get<1>(cn_c);

	return 0;
 }