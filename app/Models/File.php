<?php

namespace App\Models;

use MongoDB\Laravel\Eloquent\Model;

class File extends Model
{
    protected $connection = 'mongodb';
    protected $collection = 'files';

    protected $fillable = [
        'user_id',
        'file_name',
        'file_path',
        'file_type',
        'size',
        'status',
        'uploaded_at'
    ];

    protected $casts = [
        'uploaded_at' => 'datetime',
    ];

    public function user()
    {
        return $this->belongsTo(User::class, 'user_id', '_id');
    }
}