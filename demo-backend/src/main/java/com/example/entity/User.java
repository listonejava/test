package com.example.entity;

import javax.persistence.*;

@Entity
@Table(name = "t_user")
public class User {
    @Id
    private String id;
    
    private String name;
    
    private String email;
}
