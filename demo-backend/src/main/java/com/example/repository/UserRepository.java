package com.example.repository;

import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface UserRepository {
    List<User> findAll();
    User save(User user);
    void deleteById(String id);
}
