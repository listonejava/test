package com.example.demo.service;

import com.example.demo.entity.User;
import java.util.List;

public interface UserService {
    
    User findById(Long id);
    
    List<User> findAll();
    
    User create(User user);
    
    User update(User user);
    
    void delete(Long id);
    
    User findByUsername(String username);
}
